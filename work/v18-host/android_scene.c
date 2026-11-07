/* NativeActivity viewer for an imported real scene, not a gameplay engine.
 * Every instance owns its worker, EGL objects and input queue attachment. */
#include "amalur_scene_mesh.h"
#include "android_input_probe.h"
#include "android_scripts.h"
#include "opem_collision.h"
#include "exploration_input.h"
#include "exploration_overlay.h"
#include "scene_materials_v09.h"
#include "scene_material_renderer_v09.h"
#ifndef AMALUR_SCENE_SHA256
#define AMALUR_SCENE_SHA256 ""
#endif
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

#include "interaction_android.h"
#include "workbench_placement.inc"
#include "workbench_visual.inc"
#include "interaction_pick.h"
#include "room_lighting.h"
#include "room_lighting_shader.h"
typedef struct graphics {
    EGLDisplay display;
    EGLSurface surface;
    EGLContext context;
    GLuint program,buffer,array;
    GLint matrix_location,has_texture_location,sampler_location;
    scene_material_renderer_v09 materials;
    int ready,width,height;
    exploration_overlay overlay;
    opem_room_lighting room_lights;
} graphics;
typedef struct camera {
    float center[3],radius,distance,yaw,pitch;
    int walking,collision_ready;
    opem_collision_world *world;
    opem_controller_config body_config;
    opem_controller body;
    float walk_yaw,walk_pitch;
    /* Worker-owned debug observations, never forwarded as gameplay events. */
    int64_t pose_log_ms;
    int pose_logged,pose_grounded,pose_walking,pose_ready;
    float pose_feet[3],pose_yaw,pose_pitch,pose_distance;
    float request_right,request_forward,pose_right,pose_forward;
    uint64_t recovery_count,pose_recoveries;
} camera;
typedef struct activity_state {
    ANativeActivity *activity;
    pthread_t worker;
    pthread_mutex_t mutex;
    pthread_cond_t changed;
    int worker_started,stop,resumed,focused;
    unsigned clear_input_epoch;
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
    unsigned changes;
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
    if(changed)++host->changes;
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
    if(c->walking&&c->collision_ready){
        eye[0]=c->body.feet[0];eye[1]=c->body.feet[1];eye[2]=c->body.feet[2]+c->body_config.height*.9f;
        forward[0]=cosf(c->walk_pitch)*cosf(c->walk_yaw);forward[1]=cosf(c->walk_pitch)*sinf(c->walk_yaw);forward[2]=sinf(c->walk_pitch);
        near_plane=2.0f;cotangent=1.0f/tanf(0.6108652382f);
    }else{
        eye[0]=c->center[0]+c->distance*cp*cosf(c->yaw);
        eye[1]=c->center[1]+c->distance*cp*sinf(c->yaw);
        eye[2]=c->center[2]+c->distance*sp;
        for(i=0;i<3;i++)forward[i]=c->center[i]-eye[i];normalize3(forward);
    }
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
    const char *vertex="#version 300 es\nlayout(location=0) in vec3 p;layout(location=1) in vec3 n;layout(location=2) in vec3 c;layout(location=3) in vec2 texcoord;uniform mat4 mvp;out vec3 normal;out vec3 color;out vec2 uv;out vec3 world_position;void main(){world_position=p;gl_Position=mvp*vec4(p,1.0);normal=n;color=c;uv=texcoord;}";
    const char *fragment=opem_room_fragment;
    GLuint vs=shader(GL_VERTEX_SHADER,vertex),fs,program;GLint okay=0;
    if(!vs)return 0;fs=shader(GL_FRAGMENT_SHADER,fragment);if(!fs){glDeleteShader(vs);return 0;}
    program=glCreateProgram();glAttachShader(program,vs);glAttachShader(program,fs);glLinkProgram(program);glDeleteShader(vs);glDeleteShader(fs);
    glGetProgramiv(program,GL_LINK_STATUS,&okay);
    if(!okay){char log[2048];GLsizei written=0;glGetProgramInfoLog(program,sizeof(log)-1,&written,log);log[written]=0;LOGE("Program link: %s",log);glDeleteProgram(program);return 0;}
    return program;
}
static void graphics_close(graphics *g){
    if(g->display!=EGL_NO_DISPLAY){
        exploration_overlay_close(&g->overlay);
        scene_material_renderer_v09_close(&g->materials);
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
static int graphics_open(graphics *g,ANativeWindow *window,const amalur_scene_mesh *mesh,const scene_materials_v09 *materials){
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
        g->has_texture_location=glGetUniformLocation(g->program,"has_texture");g->sampler_location=glGetUniformLocation(g->program,"base_texture");
        if(!opem_room_lighting_open(&g->room_lights,g->program)){LOGE("Room light uniforms unavailable");goto fail;}
        LOGI("Room lighting source records=36 %s shader_equation=authored_linear_Lambert ambient_fallback=0.12 native_global_preset_pending=1",opem_room_lighting_identity());
        glGenVertexArrays(1,&g->array);glBindVertexArray(g->array);
        glGenBuffers(1,&g->buffer);glBindBuffer(GL_ARRAY_BUFFER,g->buffer);
        glBufferData(GL_ARRAY_BUFFER,(GLsizeiptr)((size_t)mesh->vertex_count*36),mesh->vertices,GL_STATIC_DRAW);
        glEnableVertexAttribArray(0);glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,36,(const void*)(uintptr_t)0);
        glEnableVertexAttribArray(1);glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,36,(const void*)(uintptr_t)12);
        glEnableVertexAttribArray(2);glVertexAttribPointer(2,3,GL_FLOAT,GL_FALSE,36,(const void*)(uintptr_t)24);
        glBindVertexArray(0);if(glGetError()!=GL_NO_ERROR)goto fail;
    }
    if(materials->uv){char error[256];
        if(scene_material_renderer_v09_open(&g->materials,materials,g->array,error,sizeof(error)))LOGI("Recovered material GPU ready textures=%u draws=%u bytes=%zu",materials->texture_count,materials->draw_count,g->materials.gpu_bytes);
        else LOGE("Material upload unavailable; fallback colors: %s",error);}
    if(!exploration_overlay_open(&g->overlay)){LOGE("Exploration overlay initialization failed");goto fail;}
    g->ready=1;LOGI("GLES scene surface ready; imported vertices=%u",mesh->vertex_count);return 1;
fail:LOGE("EGL/GLES initialization failed; EGL error=0x%x",eglGetError());graphics_close(g);return 0;
}
static int graphics_draw(graphics *g,const amalur_scene_mesh *mesh,const scene_materials_v09 *materials,const camera *c,const exploration_input *input,const oa_interaction *interaction,int room_lighting){
    EGLint width,height;
    if(!eglQuerySurface(g->display,g->surface,EGL_WIDTH,&width) || !eglQuerySurface(g->display,g->surface,EGL_HEIGHT,&height))return 0;
    if(width<=0||height<=0)return 1;g->width=width;g->height=height;glViewport(0,0,width,height);
    glClearColor(mesh->vertices?0.055f:0.17f,0.065f,0.08f,1);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
    if(mesh->vertices){float matrix[16];camera_matrix(c,(float)width/(float)height,matrix);
        glUseProgram(g->program);opem_room_lighting_upload(&g->room_lights,room_lighting);glUniformMatrix4fv(g->matrix_location,1,GL_FALSE,matrix);
        glBindVertexArray(g->array);
        if(g->materials.ready&&!scene_material_renderer_v09_draw(&g->materials,materials,g->has_texture_location,g->sampler_location)){
            LOGE("Material drawing failed; reverting to diagnostic colors");scene_material_renderer_v09_close(&g->materials);glDisableVertexAttribArray(3);
        }
        if(!g->materials.ready){glUniform1i(g->has_texture_location,0);glDrawArrays(GL_TRIANGLES,0,(GLsizei)mesh->vertex_count);}glBindVertexArray(0);}
    exploration_overlay_draw(&g->overlay,width,height,input,c->walking,c->collision_ready,interaction,room_lighting);
    if(!eglSwapBuffers(g->display,g->surface)){LOGE("EGL swap failed:0x%x",eglGetError());return 0;}
    return 1;
}
static int mesh_load(AAssetManager *manager,const char *name,amalur_scene_mesh *mesh){
    AAsset *asset=AAssetManager_open(manager,name,AASSET_MODE_STREAMING);
    unsigned char *bytes;off64_t size;size_t offset=0;char error[256];int okay;
    if(!asset){LOGE("Required mesh asset %s is absent",name);return 0;}
    size=AAsset_getLength64(asset);
    if(size<36 || (uint64_t)size>AMALUR_SCENE_MAX_BYTES){LOGE("Scene asset length is outside admitted range:%lld",(long long)size);AAsset_close(asset);return 0;}
    bytes=(unsigned char*)malloc((size_t)size);
    if(!bytes){LOGE("Scene read buffer allocation failed");AAsset_close(asset);return 0;}
    while(offset<(size_t)size){size_t wanted=(size_t)size-offset;int count;if(wanted>1048576)wanted=1048576;
        count=AAsset_read(asset,bytes+offset,wanted);if(count<=0){LOGE("Scene asset read ended early");free(bytes);AAsset_close(asset);return 0;}offset+=(size_t)count;}
    AAsset_close(asset);okay=amalur_scene_mesh_parse(bytes,(size_t)size,mesh,error,sizeof(error));free(bytes);
    if(!okay){LOGE("Scene validation failed:%s",error);return 0;}
    LOGI("Loaded mesh asset=%s vertices=%u triangles=%u bounds=(%.4f %.4f %.4f)-(%.4f %.4f %.4f)",
         name,mesh->vertex_count,mesh->vertex_count/3,mesh->bounds_min[0],mesh->bounds_min[1],mesh->bounds_min[2],
         mesh->bounds_max[0],mesh->bounds_max[1],mesh->bounds_max[2]);return 1;
}
static void materials_load(AAssetManager *manager,const amalur_scene_mesh *mesh,scene_materials_v09 *materials){
    const char *hex=AMALUR_SCENE_SHA256;unsigned char digest[32],*bytes=NULL;AAsset *asset=NULL;
    off64_t size;size_t offset=0;int i;char error[256];
    if(strlen(hex)!=64){LOGI("Materials disabled: no compiled scene identity; diagnostic colors");return;}
    for(i=0;i<32;++i){unsigned v;if(sscanf(hex+i*2,"%2x",&v)!=1){LOGE("Compiled scene identity invalid");return;}digest[i]=(unsigned char)v;}
    asset=AAssetManager_open(manager,"scene_materials.bin",AASSET_MODE_STREAMING);
    if(!asset){LOGI("Material sidecar absent; diagnostic colors");return;}
    size=AAsset_getLength64(asset);
    if(size<64||(uint64_t)size>SCENE_MATERIALS_V09_MAX_BYTES){LOGE("Material sidecar length outside bounds");goto done;}
    bytes=(unsigned char*)malloc((size_t)size);if(!bytes){LOGE("Material sidecar allocation failed");goto done;}
    while(offset<(size_t)size){size_t wanted=(size_t)size-offset;int got;if(wanted>1048576)wanted=1048576;got=AAsset_read(asset,bytes+offset,wanted);if(got<=0){LOGE("Material sidecar short read");goto done;}offset+=(size_t)got;}
    if(!scene_materials_v09_load(bytes,(size_t)size,mesh->vertex_count,digest,materials,error,sizeof(error))){LOGE("Material sidecar rejected: %s",error);goto done;}
    LOGI("Recovered material sidecar ready textures=%u draws=%u owned_bytes=%zu scene_sha256=%s opaque_preview_lighting=1",materials->texture_count,materials->draw_count,materials->owned_bytes,hex);
 done:free(bytes);AAsset_close(asset);
}
static void exploration_pose_log(camera *c,const char *reason,int force){
    int64_t now=monotonic_ms();float yaw=c->walking?c->walk_yaw:c->yaw,pitch=c->walking?c->walk_pitch:c->pitch;
    int changed=!c->pose_logged||c->body.grounded!=c->pose_grounded||c->walking!=c->pose_walking||c->collision_ready!=c->pose_ready||
        fabsf(c->body.feet[0]-c->pose_feet[0])>.01f||fabsf(c->body.feet[1]-c->pose_feet[1])>.01f||fabsf(c->body.feet[2]-c->pose_feet[2])>.01f||
        fabsf(yaw-c->pose_yaw)>.0001f||fabsf(pitch-c->pose_pitch)>.0001f||fabsf(c->distance-c->pose_distance)>.01f||
        fabsf(c->request_right-c->pose_right)>.001f||fabsf(c->request_forward-c->pose_forward)>.001f||c->recovery_count!=c->pose_recoveries;
    if(!force&&(!changed||(c->pose_logged&&now-c->pose_log_ms<1000)))return;
    LOGI("Exploration pose reason=%s observed_ms=%lld view=%s ready=%d valid=%d feet=(%.3f %.3f %.3f) grounded=%d yaw=%.5f pitch=%.5f walk_yaw=%.5f walk_pitch=%.5f request_right=%.3f request_forward=%.3f recoveries=%llu recovered_last_step=%d contacts=%u queries=%u",
        reason,(long long)now,c->walking?"walk":"overview",c->collision_ready,c->body.valid,
        c->body.feet[0],c->body.feet[1],c->body.feet[2],c->body.grounded,yaw,pitch,c->walk_yaw,c->walk_pitch,
        c->request_right,c->request_forward,(unsigned long long)c->recovery_count,c->body.recovered_last_step,c->body.contacts_last_step,c->body.queries_last_step);
    c->pose_log_ms=now;c->pose_logged=1;memcpy(c->pose_feet,c->body.feet,sizeof(c->pose_feet));
    c->pose_grounded=c->body.grounded;c->pose_walking=c->walking;c->pose_ready=c->collision_ready;
    c->pose_yaw=yaw;c->pose_pitch=pitch;c->pose_distance=c->distance;
    c->pose_right=c->request_right;c->pose_forward=c->request_forward;c->pose_recoveries=c->recovery_count;
}
static void exploration_reset(camera *c){
    /* Selected room interior hint; validated against the actual triangle mesh.
     * This is an authored exploration spawn, not a recovered player spawn. */
    const float *hint=oa_workbench_spawn_hint;char error[256];
    c->request_right=c->request_forward=0;
    if(c->world&&opem_controller_spawn(c->world,&c->body_config,hint,&c->body,error,sizeof(error))){
        c->collision_ready=1;c->walking=1;c->walk_yaw=1.5707963268f;c->walk_pitch=-.2f;
        LOGI("Exploration spawn validated feet=(%.2f %.2f %.2f) radius=%.1f height=%.1f new_host_controller=1",c->body.feet[0],c->body.feet[1],c->body.feet[2],c->body_config.radius,c->body_config.height);
    }else{c->collision_ready=0;c->walking=0;LOGE("Exploration movement unavailable: %s",c->world?error:"collision world absent");}
    exploration_pose_log(c,"reset",1);
}
static void exploration_update(camera *c,exploration_input *input,float dt){
    float right,forward,yaw,pitch;char error[256];
    if(input->reset_requested){input->reset_requested=0;exploration_reset(c);exploration_input_clear(input);}
    if(input->toggle_requested){input->toggle_requested=0;c->walking=c->collision_ready&&!c->walking;exploration_input_clear(input);LOGI("Exploration view=%s",c->walking?"walk":"overview");c->request_right=c->request_forward=0;exploration_pose_log(c,"view",1);}
    exploration_input_axes(input,&right,&forward,&yaw,&pitch);
    c->request_right=right;c->request_forward=forward;
    if(c->walking&&c->collision_ready){
        c->walk_yaw=remainderf(c->walk_yaw-input->look_dx-yaw*dt,6.283185307f);
        c->walk_pitch=clampf(c->walk_pitch-input->look_dy+pitch*dt,-1.45f,1.45f);
        if(!opem_controller_step(c->world,&c->body_config,&c->body,
            (cosf(c->walk_yaw)*forward+sinf(c->walk_yaw)*right)*c->body_config.max_speed,
            (sinf(c->walk_yaw)*forward-cosf(c->walk_yaw)*right)*c->body_config.max_speed,dt,error,sizeof(error))){
            /* Controller guarantees atomic freeze. Keep the safe view, disable
             * further walking until Reset successfully revalidates a spawn. */
            c->collision_ready=0;c->walking=0;exploration_input_clear(input);LOGE("Exploration collision step stopped: %s",error);exploration_pose_log(c,"step_failure",1);
        }else if(c->body.recovered_last_step)++c->recovery_count;
    }else{
        c->yaw=remainderf(c->yaw-input->look_dx-yaw*dt,6.283185307f);
        c->pitch=clampf(c->pitch+input->look_dy-pitch*dt,-1.4f,1.4f);
        c->distance=clampf(c->distance*expf(-forward*dt),c->radius*.05f,c->radius*40);
    }
    input->look_dx=input->look_dy=0;
    exploration_pose_log(c,"changed",0);
}
static void input_drain(AInputQueue *queue,exploration_input *input,const graphics *g,int enabled,oa_interaction *interaction,const char *inventory_path){
    AInputEvent *event;unsigned processed=0;
    while(queue&&processed++<256&&AInputQueue_getEvent(queue,&event)>=0){
        int handled=0;if(AInputQueue_preDispatchEvent(queue,event))continue;
        if(enabled){if(interaction->window_open){handled=oa_android_modal_event(interaction,event,g->width,g->height,inventory_path);exploration_input_clear(input);}else handled=exploration_input_event(input,event,g->width,g->height);}
        AInputQueue_finishEvent(queue,event,handled);
    }
}
static void *worker_main(void *argument){
    activity_state *s=(activity_state*)argument;amalur_scene_mesh mesh={0};graphics g={0};camera c={0};unsigned epoch=0,input_epoch=0;int stop,resumed,focused;
    input_host inputs={0};amalur_runtime *realm=NULL;exploration_input movement;scene_materials_v09 materials={0};
    unsigned clear_epoch=0,inventory_changes=0;int64_t last_frame_ms=0;oa_interaction interaction={0};char inventory_path[1024];int room_lighting=1;int observed_lighting_mode=-1;unsigned lighting_frames=0;int64_t lighting_started_ms=0;
    snprintf(inventory_path,sizeof(inventory_path),"%s/%s",s->activity->internalDataPath,"opem-inventory-v1.bin");
    exploration_input_clear(&movement);opem_controller_config_default(&c.body_config);
    /* Authored Workbench-area spawn: this selected indoor floor has no
     * corroborated overhead collision surface. Ground/contact and standing
     * capsule clearance remain mandatory; a missing ceiling is not a wall. */
    c.body_config.require_ceiling=0;
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
    if(!stop && mesh_load(s->activity->assetManager,"scene.bin",&mesh)){
        double radius2=0;int i;for(i=0;i<3;i++){double d=(double)mesh.bounds_max[i]-mesh.bounds_min[i];c.center[i]=(float)(((double)mesh.bounds_min[i]+mesh.bounds_max[i])*0.5);radius2+=d*d;}
        c.radius=(float)(sqrt(radius2)*0.5);c.distance=c.radius*2.5f;c.yaw=-0.7f;c.pitch=0.5f;
        {char error[256];opem_collision_stats stats;amalur_scene_mesh collision={0};
         if(mesh_load(s->activity->assetManager,"collision.bin",&collision)&&opem_collision_create(&c.world,collision.vertices,collision.vertex_count,9,error,sizeof(error))){
             opem_collision_get_stats(c.world,&stats);LOGI("Exploration recovered collision source=collision.bin scale=100 triangles=%u nodes=%u bytes=%zu",stats.triangles,stats.nodes,stats.allocated_bytes);exploration_reset(&c);
         }else LOGE("Exploration collision unavailable: source missing/invalid or controller world rejected");
         amalur_scene_mesh_clear(&collision);}
        materials_load(s->activity->assetManager,&mesh,&materials);
        realm=opem_android_scripts_start(&mesh,s->activity->assetManager,&controller);
        oa_android_start(&interaction,realm,s->activity->assetManager,inventory_path);
    }else{c.radius=1;c.distance=3;}
    for(;;){
        pthread_mutex_lock(&s->mutex);stop=s->stop;resumed=s->resumed;focused=s->focused;input_epoch=s->recreate_epoch;
        if(clear_epoch!=s->clear_input_epoch){exploration_input_clear(&movement);last_frame_ms=0;clear_epoch=s->clear_input_epoch;}
        /* Queue operations occur on this worker while holding the lifetime
         * mutex. Framework destroy callbacks wait until detach has completed. */
        if(s->attached_queue!=s->desired_queue || stop){
            exploration_input_clear(&movement);last_frame_ms=0;
            if(s->attached_queue)AInputQueue_detachLooper(s->attached_queue);
            s->attached_queue=stop?NULL:s->desired_queue;
            if(s->attached_queue)AInputQueue_attachLooper(s->attached_queue,looper,INPUT_IDENT,NULL,NULL);
            pthread_cond_broadcast(&s->changed);
        }
        /* EGL belongs solely to this worker. Holding the mutex across window
         * transitions prevents a destroy callback from retiring a pending
         * surface before the worker can finish creating/destroying it. */
        if(s->active_window!=s->desired_window || stop || (!g.ready&&epoch!=s->recreate_epoch)){
            exploration_input_clear(&movement);last_frame_ms=0;
            graphics_close(&g);if(s->active_window)ANativeWindow_release(s->active_window);
            s->active_window=stop?NULL:s->desired_window;
            if(s->active_window){ANativeWindow_acquire(s->active_window);graphics_open(&g,s->active_window,&mesh,&materials);}
            epoch=s->recreate_epoch;pthread_cond_broadcast(&s->changed);
        }
        if(stop){s->looper=NULL;pthread_cond_broadcast(&s->changed);pthread_mutex_unlock(&s->mutex);break;}
        pthread_mutex_unlock(&s->mutex);
        if(resumed){
            input_inventory_refresh(&inputs,input_epoch,0);
            if(inputs.changes!=inventory_changes){exploration_input_clear(&movement);inventory_changes=inputs.changes;}
            /* Unknown inventory cannot certify a held external device remains
             * connected. Fresh events may act for this frame; no stale hold. */
            if(!inputs.inventory_known){movement.keys=0;movement.pad_x=movement.pad_y=movement.pad_look_x=movement.pad_look_y=0;}
        }
        if(!resumed||!focused){exploration_input_clear(&movement);last_frame_ms=0;}
        {int result=ALooper_pollOnce(resumed&&g.ready?0:-1,NULL,NULL,NULL);
            if(result==INPUT_IDENT)input_drain(s->attached_queue,&movement,&g,resumed&&focused,&interaction,inventory_path);}
        /* A wake may announce teardown or a focus loss. Recheck held state. */
        pthread_mutex_lock(&s->mutex);stop=s->stop;resumed=s->resumed;focused=s->focused;
        if(clear_epoch!=s->clear_input_epoch){exploration_input_clear(&movement);last_frame_ms=0;clear_epoch=s->clear_input_epoch;}
        {int draw=!stop&&resumed&&g.ready&&s->active_window==s->desired_window;
            pthread_mutex_unlock(&s->mutex);
            if(draw){
                int64_t now=monotonic_ms();float dt=last_frame_ms?clampf((float)(now-last_frame_ms)*.001f,0,.05f):0;last_frame_ms=now;
                if(movement.lighting_requested){room_lighting=!room_lighting;movement.lighting_requested=0;LOGI("Lighting comparison mode=%s",room_lighting?"room_source_points":"legacy_preview");}
                if(focused&&!interaction.window_open)exploration_update(&c,&movement,dt);else{exploration_input_clear(&movement);last_frame_ms=0;}
                if(!interaction.window_open){
                    interaction.selected.generation=0;
                    if(c.walking&&c.collision_ready&&interaction.ready){
                        float eye[3]={c.body.feet[0],c.body.feet[1],c.body.feet[2]+c.body_config.height*.9f};
                        float direction[3]={cosf(c.walk_pitch)*cosf(c.walk_yaw),cosf(c.walk_pitch)*sinf(c.walk_yaw),sinf(c.walk_pitch)},hit[3],distance,occlusion;
                        if(oa_mesh_pick(mesh.vertices,mesh.vertex_count,OA_WORKBENCH_FIRST_VERTEX,OA_WORKBENCH_VERTEX_COUNT,eye,direction,300,hit,&distance)&&opem_collision_ray(c.world,eye,direction,300,&occlusion)&&occlusion+.5f>=distance&&oa_object_target(&interaction.registry,interaction.workbench,hit)&&oa_workbench_in_reach(&interaction.registry,interaction.workbench,c.body.feet,c.walk_yaw))interaction.selected=interaction.workbench;
                    }
                    if(movement.interact_requested){char error[256];movement.interact_requested=0;if(interaction.selected.generation){if(oa_lua_interact(realm,&interaction,error,sizeof(error)))LOGE("Workbench original Lua callback failed: %s",error);else{LOGI("Workbench original Lua on_interact opened authored alchemy window source=524875");exploration_input_clear(&movement);}}}
                }
                if(observed_lighting_mode!=room_lighting||!lighting_started_ms){observed_lighting_mode=room_lighting;lighting_started_ms=now;lighting_frames=0;}
                if(++lighting_frames==120){LOGI("Lighting frame observation mode=%s frames=120 elapsed_ms=%lld mean_interval_ms=%.3f scope=active_worker_frame_intervals",room_lighting?"room":"preview",(long long)(now-lighting_started_ms),(double)(now-lighting_started_ms)/119.0);}
                if(!graphics_draw(&g,&mesh,&materials,&c,&movement,&interaction,room_lighting)){pthread_mutex_lock(&s->mutex);graphics_close(&g);pthread_mutex_unlock(&s->mutex);}
            }else last_frame_ms=0;
        }
    }
    opem_android_scripts_stop(realm);
    oa_android_close(&interaction);
    input_host_close(&inputs,s->activity->vm);
    scene_materials_v09_free(&materials);
    opem_collision_destroy(c.world);
    amalur_scene_mesh_clear(&mesh);ALooper_release(looper);return NULL;
}
static void on_resume(ANativeActivity *activity){activity_state *s=(activity_state*)activity->instance;if(!s)return;pthread_mutex_lock(&s->mutex);s->resumed=1;s->recreate_epoch++;wake_locked(s);pthread_mutex_unlock(&s->mutex);}
static void on_pause(ANativeActivity *activity){activity_state *s=(activity_state*)activity->instance;if(!s)return;pthread_mutex_lock(&s->mutex);s->resumed=0;s->clear_input_epoch++;wake_locked(s);pthread_mutex_unlock(&s->mutex);}
static void on_focus(ANativeActivity *activity,int focused){activity_state *s=(activity_state*)activity->instance;if(!s)return;pthread_mutex_lock(&s->mutex);s->focused=focused;if(!focused)s->clear_input_epoch++;wake_locked(s);pthread_mutex_unlock(&s->mutex);}
static void on_configuration(ANativeActivity *activity){activity_state *s=(activity_state*)activity->instance;if(!s)return;pthread_mutex_lock(&s->mutex);s->recreate_epoch++;s->clear_input_epoch++;wake_locked(s);pthread_mutex_unlock(&s->mutex);}
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
    activity->callbacks->onResume=on_resume;activity->callbacks->onPause=on_pause;activity->callbacks->onWindowFocusChanged=on_focus;
    activity->callbacks->onConfigurationChanged=on_configuration;
    activity->callbacks->onNativeWindowCreated=on_window_created;activity->callbacks->onNativeWindowDestroyed=on_window_destroyed;
    activity->callbacks->onInputQueueCreated=on_queue_created;activity->callbacks->onInputQueueDestroyed=on_queue_destroyed;
    activity->callbacks->onDestroy=on_destroy;
    if(pthread_create(&s->worker,NULL,worker_main,s)){LOGE("Scene worker creation failed");ANativeActivity_finish(activity);return;}
    s->worker_started=1;
}
