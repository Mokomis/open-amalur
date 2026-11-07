/* NativeActivity viewer for an imported real scene, not a gameplay engine.
 * Every instance owns its worker, EGL objects and input queue attachment. */
#include "amalur_scene_mesh.h"
#include "android_input_probe.h"
#include "android_scripts.h"
#include <android/native_activity.h>
#include <android/native_window.h>
#include <android/asset_manager.h>
#include <android/input.h>
#include <android/looper.h>
#include <android/log.h>
#include <EGL/egl.h>
#include <GLES3/gl3.h>
#include <pthread.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdint.h>
#include <time.h>

#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,"OpemAmalurScene",__VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScene",__VA_ARGS__)
#define INPUT_IDENT 1

typedef struct graphics {
    EGLDisplay display;
    EGLSurface surface;
    EGLContext context;
    GLuint program,buffer,array;
    GLint matrix_location;
    int ready,width,height;
} graphics;
typedef struct camera {
    float center[3],radius,distance,yaw,pitch;
    float last_x,last_y,last_pinch;
    int dragging;
} camera;
typedef struct activity_state {
    ANativeActivity *activity;
    pthread_t worker;
    pthread_mutex_t mutex;
    pthread_cond_t changed;
    int worker_started,stop,resumed;
    unsigned recreate_epoch;
    ALooper *looper;                  /* Shared reference protected by mutex. */
    ANativeWindow *desired_window;    /* Main callback owns an acquired ref. */
    ANativeWindow *active_window;     /* Worker owns a separate acquired ref. */
    AInputQueue *desired_queue;       /* Framework lifetime, detach before return. */
    AInputQueue *attached_queue;      /* Only worker attaches/detaches. */
} activity_state;

/* Worker-only JNI and inventory storage. A connection snapshot is independent
 * of the explicit Android logical-button policy and never sets native kinds. */
typedef struct input_host {
    JNIEnv *env;
    int detach_on_exit;
    int inventory_known,inventory_logged;
    unsigned refresh_epoch;
    int64_t last_check_ms;
    opem_android_inventory inventory;
} input_host;

static int64_t monotonic_ms(void){
    struct timespec now;if(clock_gettime(CLOCK_MONOTONIC,&now))return 0;
    return (int64_t)now.tv_sec*1000+(int64_t)now.tv_nsec/1000000;
}
static void input_host_open(input_host *host,JavaVM *vm){
    jint result;
    if(!vm){LOGE("Input inventory unknown: Activity has no JavaVM");return;}
    result=(*vm)->GetEnv(vm,(void**)&host->env,JNI_VERSION_1_6);
    if(result==JNI_EDETACHED){
        if((*vm)->AttachCurrentThread(vm,&host->env,NULL)!=JNI_OK){
            host->env=NULL;LOGE("Input inventory unknown: worker JNI attach failed");return;
        }
        host->detach_on_exit=1;
    }else if(result!=JNI_OK){host->env=NULL;LOGE("Input inventory unknown: worker GetEnv failed (%d)",result);}
}
static int device_compare(const void *a,const void *b){
    const opem_android_device *left=(const opem_android_device*)a,*right=(const opem_android_device*)b;
    return (left->id>right->id)-(left->id<right->id);
}
static void input_inventory_refresh(input_host *host,unsigned epoch,int force){
    opem_android_inventory current;size_t i;unsigned gamepads=0,keyboards=0,touchscreens=0;
    int known,changed;int64_t now;
    if(!host->env)return;
    now=monotonic_ms();
    if(!force&&host->inventory_logged&&host->refresh_epoch==epoch&&now-host->last_check_ms<500)return;
    host->last_check_ms=now;host->refresh_epoch=epoch;
    known=opem_android_inventory_read(host->env,&current);
    if(known)qsort(current.devices,current.count,sizeof(current.devices[0]),device_compare);
    changed=!host->inventory_logged||known!=host->inventory_known;
    if(known&&!changed){
        changed=current.count!=host->inventory.count;
        for(i=0;i<current.count&&!changed;++i){
            const opem_android_device *a=&current.devices[i],*b=&host->inventory.devices[i];
            changed=a->id!=b->id||a->sources!=b->sources||a->is_virtual!=b->is_virtual;
        }
    }
    host->inventory_known=known;host->inventory_logged=1;
    if(!known){
        if(changed)LOGE("Input inventory unknown: JNI query failed, changed during enumeration, or exceeded bound");
        return;
    }
    host->inventory=current;
    if(!changed)return;
    for(i=0;i<current.count;++i){
        int32_t sources=current.devices[i].sources;
        if((sources&AINPUT_SOURCE_GAMEPAD)==AINPUT_SOURCE_GAMEPAD||
           (sources&AINPUT_SOURCE_JOYSTICK)==AINPUT_SOURCE_JOYSTICK)++gamepads;
        if((sources&AINPUT_SOURCE_KEYBOARD)==AINPUT_SOURCE_KEYBOARD)++keyboards;
        if((sources&AINPUT_SOURCE_TOUCHSCREEN)==AINPUT_SOURCE_TOUCHSCREEN)++touchscreens;
    }
    LOGI("Input inventory known: devices=%zu controller_sources=%u keyboard_sources=%u touchscreen_sources=%u observed_ms=%lld policy_independent=1",
         current.count,gamepads,keyboards,touchscreens,(long long)now);
    for(i=0;i<current.count;++i)LOGI("Input device id=%d sources=0x%x virtual=%d",
        current.devices[i].id,(unsigned)current.devices[i].sources,current.devices[i].is_virtual);
}
static void input_host_close(input_host *host,JavaVM *vm){
    if(host->detach_on_exit&&vm){
        if((*vm)->DetachCurrentThread(vm)!=JNI_OK)LOGE("Worker JNI detach failed");
    }
    host->env=NULL;host->detach_on_exit=0;
}

static float clampf(float x,float lo,float hi){return x<lo?lo:x>hi?hi:x;}
static void wake_locked(activity_state *s){if(s->looper)ALooper_wake(s->looper);}
static void normalize3(float v[3]){float n=sqrtf(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);if(n>0){v[0]/=n;v[1]/=n;v[2]/=n;}}
static void cross3(const float a[3],const float b[3],float out[3]){out[0]=a[1]*b[2]-a[2]*b[1];out[1]=a[2]*b[0]-a[0]*b[2];out[2]=a[0]*b[1]-a[1]*b[0];}
static float dot3(const float a[3],const float b[3]){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static void multiply4(float out[16],const float a[16],const float b[16]){
    int row,col,k;float result[16];for(col=0;col<4;col++)for(row=0;row<4;row++){
        float value=0;for(k=0;k<4;k++)value+=a[k*4+row]*b[col*4+k];result[col*4+row]=value;}
    memcpy(out,result,sizeof(result));
}
static void camera_matrix(const camera *c,float aspect,float output[16]){
    float eye[3],forward[3],side[3],up[3],world_up[3]={0,0,1};
    float view[16]={0},projection[16]={0};float cp=cosf(c->pitch),sp=sinf(c->pitch);
    float near_plane=fmaxf(c->radius*0.001f,1e-7f),far_plane=c->distance+c->radius*40.0f;
    float cotangent=1.0f/tanf(0.3926990817f);int i;
    far_plane=fmaxf(far_plane,near_plane*2.0f);
    eye[0]=c->center[0]+c->distance*cp*cosf(c->yaw);
    eye[1]=c->center[1]+c->distance*cp*sinf(c->yaw);
    eye[2]=c->center[2]+c->distance*sp;
    for(i=0;i<3;i++)forward[i]=c->center[i]-eye[i];normalize3(forward);
    cross3(forward,world_up,side);normalize3(side);cross3(side,forward,up);
    view[0]=side[0];view[4]=side[1];view[8]=side[2];view[12]=-dot3(side,eye);
    view[1]=up[0];view[5]=up[1];view[9]=up[2];view[13]=-dot3(up,eye);
    view[2]=-forward[0];view[6]=-forward[1];view[10]=-forward[2];view[14]=dot3(forward,eye);view[15]=1;
    projection[0]=cotangent/aspect;projection[5]=cotangent;
    projection[10]=(far_plane+near_plane)/(near_plane-far_plane);
    projection[11]=-1;projection[14]=(2*far_plane*near_plane)/(near_plane-far_plane);
    multiply4(output,projection,view);
}
static GLuint shader(GLenum type,const char *source){
    GLuint object=glCreateShader(type);GLint okay=0;
    glShaderSource(object,1,&source,NULL);glCompileShader(object);glGetShaderiv(object,GL_COMPILE_STATUS,&okay);
    if(!okay){char log[2048];GLsizei written=0;glGetShaderInfoLog(object,sizeof(log)-1,&written,log);log[written]=0;LOGE("Shader compile: %s",log);glDeleteShader(object);return 0;}
    return object;
}
static GLuint program_create(void){
    const char *vertex="#version 300 es\nlayout(location=0) in vec3 p;layout(location=1) in vec3 n;layout(location=2) in vec3 c;uniform mat4 mvp;out vec3 normal;out vec3 color;void main(){gl_Position=mvp*vec4(p,1.0);normal=n;color=c;}";
    const char *fragment="#version 300 es\nprecision highp float;in vec3 normal;in vec3 color;out vec4 outColor;void main(){float n=length(normal);vec3 unitNormal=n>0.000001?normal/n:vec3(0.0);float light=0.35+0.65*max(dot(unitNormal,normalize(vec3(0.35,-0.2,0.9))),0.0);outColor=vec4(clamp(color,0.0,1.0)*light,1.0);}";
    GLuint vs=shader(GL_VERTEX_SHADER,vertex),fs,program;GLint okay=0;
    if(!vs)return 0;fs=shader(GL_FRAGMENT_SHADER,fragment);if(!fs){glDeleteShader(vs);return 0;}
    program=glCreateProgram();glAttachShader(program,vs);glAttachShader(program,fs);glLinkProgram(program);glDeleteShader(vs);glDeleteShader(fs);
    glGetProgramiv(program,GL_LINK_STATUS,&okay);
    if(!okay){char log[2048];GLsizei written=0;glGetProgramInfoLog(program,sizeof(log)-1,&written,log);log[written]=0;LOGE("Program link: %s",log);glDeleteProgram(program);return 0;}
    return program;
}
static void graphics_close(graphics *g){
    if(g->display!=EGL_NO_DISPLAY){
        if(g->buffer)glDeleteBuffers(1,&g->buffer);
        if(g->array)glDeleteVertexArrays(1,&g->array);
        if(g->program)glDeleteProgram(g->program);
        eglMakeCurrent(g->display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);
        if(g->surface!=EGL_NO_SURFACE)eglDestroySurface(g->display,g->surface);
        if(g->context!=EGL_NO_CONTEXT)eglDestroyContext(g->display,g->context);
        eglTerminate(g->display);
    }
    memset(g,0,sizeof(*g));g->display=EGL_NO_DISPLAY;g->surface=EGL_NO_SURFACE;g->context=EGL_NO_CONTEXT;
}
static int graphics_open(graphics *g,ANativeWindow *window,const amalur_scene_mesh *mesh){
    EGLConfig config;EGLint configurations=0,format=0;
    const EGLint attributes[]={EGL_SURFACE_TYPE,EGL_WINDOW_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES3_BIT,
        EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_DEPTH_SIZE,24,EGL_NONE};
    const EGLint context_attributes[]={EGL_CONTEXT_CLIENT_VERSION,3,EGL_NONE};
    g->display=eglGetDisplay(EGL_DEFAULT_DISPLAY);
    if(g->display==EGL_NO_DISPLAY || !eglInitialize(g->display,NULL,NULL))goto fail;
    if(!eglBindAPI(EGL_OPENGL_ES_API) || !eglChooseConfig(g->display,attributes,&config,1,&configurations) || !configurations)goto fail;
    if(!eglGetConfigAttrib(g->display,config,EGL_NATIVE_VISUAL_ID,&format) || ANativeWindow_setBuffersGeometry(window,0,0,format)!=0)goto fail;
    g->surface=eglCreateWindowSurface(g->display,config,window,NULL);
    if(g->surface==EGL_NO_SURFACE)goto fail;
    g->context=eglCreateContext(g->display,config,EGL_NO_CONTEXT,context_attributes);
    if(g->context==EGL_NO_CONTEXT || !eglMakeCurrent(g->display,g->surface,g->surface,g->context))goto fail;
    eglSwapInterval(g->display,1);
    glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LEQUAL);glDisable(GL_CULL_FACE);
    if(mesh->vertices){
        g->program=program_create();if(!g->program)goto fail;
        g->matrix_location=glGetUniformLocation(g->program,"mvp");
        glGenVertexArrays(1,&g->array);glBindVertexArray(g->array);
        glGenBuffers(1,&g->buffer);glBindBuffer(GL_ARRAY_BUFFER,g->buffer);
        glBufferData(GL_ARRAY_BUFFER,(GLsizeiptr)((size_t)mesh->vertex_count*36),mesh->vertices,GL_STATIC_DRAW);
        glEnableVertexAttribArray(0);glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,36,(const void*)(uintptr_t)0);
        glEnableVertexAttribArray(1);glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,36,(const void*)(uintptr_t)12);
        glEnableVertexAttribArray(2);glVertexAttribPointer(2,3,GL_FLOAT,GL_FALSE,36,(const void*)(uintptr_t)24);
        glBindVertexArray(0);if(glGetError()!=GL_NO_ERROR)goto fail;
    }
    g->ready=1;LOGI("GLES scene surface ready; imported vertices=%u",mesh->vertex_count);return 1;
fail:LOGE("EGL/GLES initialization failed; EGL error=0x%x",eglGetError());graphics_close(g);return 0;
}
static int graphics_draw(graphics *g,const amalur_scene_mesh *mesh,const camera *c){
    EGLint width,height;
    if(!eglQuerySurface(g->display,g->surface,EGL_WIDTH,&width) || !eglQuerySurface(g->display,g->surface,EGL_HEIGHT,&height))return 0;
    if(width<=0||height<=0)return 1;g->width=width;g->height=height;glViewport(0,0,width,height);
    glClearColor(mesh->vertices?0.055f:0.17f,0.065f,0.08f,1);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
    if(mesh->vertices){float matrix[16];camera_matrix(c,(float)width/(float)height,matrix);
        glUseProgram(g->program);glUniformMatrix4fv(g->matrix_location,1,GL_FALSE,matrix);
        glBindVertexArray(g->array);glDrawArrays(GL_TRIANGLES,0,(GLsizei)mesh->vertex_count);glBindVertexArray(0);}
    if(!eglSwapBuffers(g->display,g->surface)){LOGE("EGL swap failed:0x%x",eglGetError());return 0;}
    return 1;
}
static int mesh_load(AAssetManager *manager,amalur_scene_mesh *mesh){
    AAsset *asset=AAssetManager_open(manager,"scene.bin",AASSET_MODE_STREAMING);
    unsigned char *bytes;off64_t size;size_t offset=0;char error[256];int okay;
    if(!asset){LOGE("Required real scene asset scene.bin is absent");return 0;}
    size=AAsset_getLength64(asset);
    if(size<36 || (uint64_t)size>AMALUR_SCENE_MAX_BYTES){LOGE("Scene asset length is outside admitted range:%lld",(long long)size);AAsset_close(asset);return 0;}
    bytes=(unsigned char*)malloc((size_t)size);
    if(!bytes){LOGE("Scene read buffer allocation failed");AAsset_close(asset);return 0;}
    while(offset<(size_t)size){size_t wanted=(size_t)size-offset;int count;if(wanted>1048576)wanted=1048576;
        count=AAsset_read(asset,bytes+offset,wanted);if(count<=0){LOGE("Scene asset read ended early");free(bytes);AAsset_close(asset);return 0;}offset+=(size_t)count;}
    AAsset_close(asset);okay=amalur_scene_mesh_parse(bytes,(size_t)size,mesh,error,sizeof(error));free(bytes);
    if(!okay){LOGE("Scene validation failed:%s",error);return 0;}
    LOGI("Loaded real scene interchange:vertices=%u triangles=%u bounds=(%.4f %.4f %.4f)-(%.4f %.4f %.4f)",
         mesh->vertex_count,mesh->vertex_count/3,mesh->bounds_min[0],mesh->bounds_min[1],mesh->bounds_min[2],
         mesh->bounds_max[0],mesh->bounds_max[1],mesh->bounds_max[2]);return 1;
}
static int input_motion(AInputEvent *event,camera *c){
    int action=AMotionEvent_getAction(event)&AMOTION_EVENT_ACTION_MASK;size_t pointers=AMotionEvent_getPointerCount(event);
    if(!pointers)return 0;
    if(action==AMOTION_EVENT_ACTION_UP||action==AMOTION_EVENT_ACTION_CANCEL||action==AMOTION_EVENT_ACTION_POINTER_UP){c->dragging=0;c->last_pinch=0;return 1;}
    if(pointers>=2){
        float dx=AMotionEvent_getX(event,0)-AMotionEvent_getX(event,1),dy=AMotionEvent_getY(event,0)-AMotionEvent_getY(event,1);
        float pinch=sqrtf(dx*dx+dy*dy);
        if(action==AMOTION_EVENT_ACTION_MOVE && c->last_pinch>1 && pinch>1)c->distance=clampf(c->distance*c->last_pinch/pinch,c->radius*0.05f,c->radius*40.0f);
        c->last_pinch=pinch;c->dragging=0;return 1;
    }
    {float x=AMotionEvent_getX(event,0),y=AMotionEvent_getY(event,0);
        if(action==AMOTION_EVENT_ACTION_MOVE&&c->dragging){c->yaw-=(x-c->last_x)*0.005f;c->pitch=clampf(c->pitch+(y-c->last_y)*0.005f,-1.4f,1.4f);}
        c->last_x=x;c->last_y=y;c->dragging=1;c->last_pinch=0;}
    return 1;
}
static void input_drain(AInputQueue *queue,camera *c){
    AInputEvent *event;unsigned processed=0;
    while(queue && processed++<256 && AInputQueue_getEvent(queue,&event)>=0){
        int handled=0;if(AInputQueue_preDispatchEvent(queue,event))continue;
        /* Joystick and mouse motion are not touchscreen coordinates. Merely
         * observing an event is not consumption; keys stay unhandled until
         * this viewer has a real action for them. */
        if(opem_android_event_family(event)==OPEM_INPUT_TOUCH)handled=input_motion(event,c);
        AInputQueue_finishEvent(queue,event,handled);
    }
}
static void *worker_main(void *argument){
    activity_state *s=(activity_state*)argument;amalur_scene_mesh mesh={0};graphics g={0};camera c={0};unsigned epoch=0,input_epoch=0;int stop,resumed;
    input_host inputs={0};amalur_runtime *realm=NULL;
    /* Explicit new Android menu policy, independent of controller presence,
     * native kinds, locale, and button glyphs. No native-kind inference. */
    scene_controller_state_v08 controller={1,0,SCENE_CONTROLLER_DOMAIN_ANDROID_LOGICAL_STANDARD};
    ALooper *looper=ALooper_prepare(ALOOPER_PREPARE_ALLOW_NON_CALLBACKS);
    g.display=EGL_NO_DISPLAY;g.surface=EGL_NO_SURFACE;g.context=EGL_NO_CONTEXT;
    if(!looper){LOGE("Could not prepare scene looper");return NULL;}
    ALooper_acquire(looper);pthread_mutex_lock(&s->mutex);s->looper=looper;stop=s->stop;pthread_mutex_unlock(&s->mutex);
    if(!stop){
        input_host_open(&inputs,s->activity->vm);input_inventory_refresh(&inputs,0,1);
        LOGI("Controller policy domain=ANDROID_LOGICAL_STANDARD is_set=%d Android_A=confirm Android_B=back native_kind_unassigned=1",controller.is_set);
    }
    if(!stop && mesh_load(s->activity->assetManager,&mesh)){
        double radius2=0;int i;for(i=0;i<3;i++){double d=(double)mesh.bounds_max[i]-mesh.bounds_min[i];c.center[i]=(float)(((double)mesh.bounds_min[i]+mesh.bounds_max[i])*0.5);radius2+=d*d;}
        c.radius=(float)(sqrt(radius2)*0.5);c.distance=c.radius*2.5f;c.yaw=-0.7f;c.pitch=0.5f;
        realm=opem_android_scripts_start(&mesh,s->activity->assetManager,&controller);
    }else{c.radius=1;c.distance=3;}
    for(;;){
        pthread_mutex_lock(&s->mutex);stop=s->stop;resumed=s->resumed;input_epoch=s->recreate_epoch;
        /* Queue operations occur on this worker while holding the lifetime
         * mutex. Framework destroy callbacks wait until detach has completed. */
        if(s->attached_queue!=s->desired_queue || stop){
            c.dragging=0;c.last_pinch=0;
            if(s->attached_queue)AInputQueue_detachLooper(s->attached_queue);
            s->attached_queue=stop?NULL:s->desired_queue;
            if(s->attached_queue)AInputQueue_attachLooper(s->attached_queue,looper,INPUT_IDENT,NULL,NULL);
            pthread_cond_broadcast(&s->changed);
        }
        /* EGL belongs solely to this worker. Holding the mutex across window
         * transitions prevents a destroy callback from retiring a pending
         * surface before the worker can finish creating/destroying it. */
        if(s->active_window!=s->desired_window || stop || (!g.ready&&epoch!=s->recreate_epoch)){
            graphics_close(&g);if(s->active_window)ANativeWindow_release(s->active_window);
            s->active_window=stop?NULL:s->desired_window;
            if(s->active_window){ANativeWindow_acquire(s->active_window);graphics_open(&g,s->active_window,&mesh);}
            epoch=s->recreate_epoch;pthread_cond_broadcast(&s->changed);
        }
        if(stop){s->looper=NULL;pthread_cond_broadcast(&s->changed);pthread_mutex_unlock(&s->mutex);break;}
        pthread_mutex_unlock(&s->mutex);
        if(resumed)input_inventory_refresh(&inputs,input_epoch,0);
        else{c.dragging=0;c.last_pinch=0;}
        {int result=ALooper_pollOnce(resumed&&g.ready?0:-1,NULL,NULL,NULL);
            if(result==INPUT_IDENT)input_drain(s->attached_queue,&c);}
        /* A wake may announce teardown. Recheck before touching the surface. */
        pthread_mutex_lock(&s->mutex);stop=s->stop;resumed=s->resumed;
        {int draw=!stop&&resumed&&g.ready&&s->active_window==s->desired_window;
            pthread_mutex_unlock(&s->mutex);
            if(draw&&!graphics_draw(&g,&mesh,&c)){pthread_mutex_lock(&s->mutex);graphics_close(&g);pthread_mutex_unlock(&s->mutex);}}
    }
    opem_android_scripts_stop(realm);
    input_host_close(&inputs,s->activity->vm);
    amalur_scene_mesh_clear(&mesh);ALooper_release(looper);return NULL;
}
static void on_resume(ANativeActivity *activity){activity_state *s=(activity_state*)activity->instance;if(!s)return;pthread_mutex_lock(&s->mutex);s->resumed=1;s->recreate_epoch++;wake_locked(s);pthread_mutex_unlock(&s->mutex);}
static void on_pause(ANativeActivity *activity){activity_state *s=(activity_state*)activity->instance;if(!s)return;pthread_mutex_lock(&s->mutex);s->resumed=0;wake_locked(s);pthread_mutex_unlock(&s->mutex);}
static void on_configuration(ANativeActivity *activity){activity_state *s=(activity_state*)activity->instance;if(!s)return;pthread_mutex_lock(&s->mutex);s->recreate_epoch++;wake_locked(s);pthread_mutex_unlock(&s->mutex);}
static void on_window_created(ANativeActivity *activity,ANativeWindow *window){
    activity_state *s=(activity_state*)activity->instance;ANativeWindow *old;if(!s)return;
    ANativeWindow_acquire(window);pthread_mutex_lock(&s->mutex);old=s->desired_window;s->desired_window=window;s->recreate_epoch++;wake_locked(s);pthread_mutex_unlock(&s->mutex);if(old)ANativeWindow_release(old);
}
static void on_window_destroyed(ANativeActivity *activity,ANativeWindow *window){
    activity_state *s=(activity_state*)activity->instance;int release=0;if(!s)return;
    pthread_mutex_lock(&s->mutex);if(s->desired_window==window){s->desired_window=NULL;release=1;}wake_locked(s);
    while(s->active_window==window)pthread_cond_wait(&s->changed,&s->mutex);
    pthread_mutex_unlock(&s->mutex);if(release)ANativeWindow_release(window);
}
static void on_queue_created(ANativeActivity *activity,AInputQueue *queue){activity_state *s=(activity_state*)activity->instance;if(!s)return;pthread_mutex_lock(&s->mutex);s->desired_queue=queue;wake_locked(s);pthread_mutex_unlock(&s->mutex);}
static void on_queue_destroyed(ANativeActivity *activity,AInputQueue *queue){
    activity_state *s=(activity_state*)activity->instance;if(!s)return;
    pthread_mutex_lock(&s->mutex);if(s->desired_queue==queue)s->desired_queue=NULL;wake_locked(s);
    while(s->attached_queue==queue)pthread_cond_wait(&s->changed,&s->mutex);pthread_mutex_unlock(&s->mutex);
}
static void on_destroy(ANativeActivity *activity){
    activity_state *s=(activity_state*)activity->instance;if(!s)return;
    pthread_mutex_lock(&s->mutex);s->stop=1;s->desired_queue=NULL;wake_locked(s);pthread_mutex_unlock(&s->mutex);
    if(s->worker_started)pthread_join(s->worker,NULL);
    if(s->desired_window)ANativeWindow_release(s->desired_window);
    pthread_cond_destroy(&s->changed);pthread_mutex_destroy(&s->mutex);activity->instance=NULL;free(s);
}
__attribute__((visibility("default")))
void ANativeActivity_onCreate(ANativeActivity *activity,void *saved_state,size_t saved_size){
    activity_state *s=(activity_state*)calloc(1,sizeof(*s));(void)saved_state;(void)saved_size;
    if(!s){LOGE("Activity state allocation failed");ANativeActivity_finish(activity);return;}
    if(pthread_mutex_init(&s->mutex,NULL)){free(s);ANativeActivity_finish(activity);return;}
    if(pthread_cond_init(&s->changed,NULL)){pthread_mutex_destroy(&s->mutex);free(s);ANativeActivity_finish(activity);return;}
    s->activity=activity;activity->instance=s;
    activity->callbacks->onResume=on_resume;activity->callbacks->onPause=on_pause;
    activity->callbacks->onConfigurationChanged=on_configuration;
    activity->callbacks->onNativeWindowCreated=on_window_created;activity->callbacks->onNativeWindowDestroyed=on_window_destroyed;
    activity->callbacks->onInputQueueCreated=on_queue_created;activity->callbacks->onInputQueueDestroyed=on_queue_destroyed;
    activity->callbacks->onDestroy=on_destroy;
    if(pthread_create(&s->worker,NULL,worker_main,s)){LOGE("Scene worker creation failed");ANativeActivity_finish(activity);return;}
    s->worker_started=1;
}
