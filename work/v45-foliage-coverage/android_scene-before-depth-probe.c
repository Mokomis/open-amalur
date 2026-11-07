/* NativeActivity viewer for an imported real scene, not a gameplay engine.
 * Every instance owns its worker, EGL objects and input queue attachment. */
#include "amalur_scene_mesh.h"
#ifdef OA_DESKTOP
#include "desktop_capture.h"
#endif
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
#include "oa_character_gl.h"
#include "oa_npc.h"
#include "oa_combat.h"
#include "oa_sky.h"
#include "oa_ui.h"
#include "oa_menu.h"
#include <ctype.h>
#include "oa_items.h"
#include "oa_stream.h"
#include "oa_post.h"
#include "oa_native_water.h"
#include "oa_native_shadow.h"
#include "oa_native_sky.h"
#include "oa_native_ao_math.h"
#include "native_foliage_wind.h"
#include "oa_actors.h"
#include "oa_audio.h"
#include "oa_fx.h"
#include "town_live.inc"
#include "town_start.inc"
#include <dlfcn.h>
#include "town_identity.h"
#include <sys/system_properties.h>
/* Door positions come from int_dal_gorhart_alchemistshop_entrance and _exit object records.
 * World 0 is the shop, world 1 is Gorhart. Prompt radius is authored. */
static const float oa_doors[2][3]={{-342.4f,-139.6f,0.0f},{OA_LIVE_START_X,OA_LIVE_START_Y,OA_LIVE_START_Z}};
/* Authored spawn in the open field ahead of the door, because the bandit has no pathfinding. */
#define OA_FOE_SPAWN_X (OA_LIVE_START_X+424.9f)
#define OA_FOE_SPAWN_Y (OA_LIVE_START_Y+1059.2f)
static const char *const oa_door_prompts[2]={"EXIT - INTERACT","ENTER SHOP"};
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
    oa_character_gpu character;
    oa_character_gpu people[OA_NPC_MAX];
    oa_character_gpu foe;
    oa_sky sky;
    oa_ui ui;
    GLuint shadow_fbo,shadow_tex,world_program,world_programs[7];oa_lightgrid light_grid;
    oa_post post;oa_native_water native_water;oa_native_shadow native_shadow;oa_native_sky native_sky;int native_observed;
} graphics;
/* Worker-only streamed world while outdoors. */
static oa_audio *active_audio;static oa_fx *active_fx;static AAssetManager *fx_manager;static int fx_tried;static int snd_foot=-1,snd_use=-1,snd_hit=-1,snd_die=-1;static unsigned tour_frames,tour_air,tour_reached,tour_gave_up,tour_detours;static oa_actors *active_actors;static oa_stream *active_stream;static float stream_far=100000.0f;
/* Worker-only UI asset, kept for surface recreation. */
static uint8_t *ui_bytes;static size_t ui_size;
typedef struct camera {
    float center[3],radius,distance,yaw,pitch;
    int walking,collision_ready;
    opem_collision_world *world;
    opem_controller_config body_config;
    opem_controller body;
    float walk_yaw,walk_pitch,boom;
    const float *spawn_hint;
    oa_character character;
    oa_npcs npcs;
    /* Fight state. Exists only outdoors. */
    oa_character foe;
    opem_controller foe_body;
    oa_combat combat;
    int foe_ready;
    uint8_t *sky_bytes;
    size_t sky_size;
    int64_t foe_log_ms;
    float foe_detour,foe_detour_side,foe_stuck;
    float move_scale,look_speed;
    int invert_look;
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
#define OA_CAMERA_PIVOT 150.0f
#define OA_CAMERA_BOOM 240.0f
static void camera_matrix(const camera *c,float aspect,float output[16],float eye_out[3]){
#ifdef OA_DESKTOP
    if(oa_desktop_reference_camera(output,eye_out))return;
#endif
    float eye[3],forward[3],side[3],up[3],world_up[3]={0,0,1};
    float view[16]={0},projection[16]={0};float cp=cosf(c->pitch),sp=sinf(c->pitch);
    float near_plane=fmaxf(c->radius*0.001f,1e-7f),far_plane=active_stream&&c->walking?stream_far*1.6f:c->distance+c->radius*40.0f;
    float cotangent=1.0f/tanf(0.3926990817f);int i;
    far_plane=fmaxf(far_plane,near_plane*2.0f);
    if(c->walking&&c->collision_ready){
        forward[0]=cosf(c->walk_pitch)*cosf(c->walk_yaw);forward[1]=cosf(c->walk_pitch)*sinf(c->walk_yaw);forward[2]=sinf(c->walk_pitch);
        /* Authored third-person boom behind the character; c->boom is collision-limited. */
        eye[0]=c->body.feet[0]-forward[0]*c->boom;eye[1]=c->body.feet[1]-forward[1]*c->boom;eye[2]=fmaxf(c->body.feet[2]+OA_CAMERA_PIVOT-forward[2]*c->boom,c->body.feet[2]+40.0f);
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
    memcpy(eye_out,eye,sizeof(eye));
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
        oa_fx_close(active_fx);active_fx=NULL;fx_tried=0;oa_actors_gpu_close(active_actors);exploration_overlay_close(&g->overlay);oa_ui_close(&g->ui);oa_stream_gpu_close(active_stream);oa_post_close(&g->post);oa_native_water_close(&g->native_water);oa_native_shadow_close(&g->native_shadow);oa_native_sky_close(&g->native_sky);{int wi;for(wi=0;wi<7;wi++)if(g->world_programs[wi])glDeleteProgram(g->world_programs[wi]);g->world_program=0;}oa_lightgrid_close(&g->light_grid);if(g->shadow_tex)glDeleteTextures(1,&g->shadow_tex);if(g->shadow_fbo)glDeleteFramebuffers(1,&g->shadow_fbo);
        scene_material_renderer_v09_close(&g->materials);
        if(g->buffer)glDeleteBuffers(1,&g->buffer);
        if(g->array)glDeleteVertexArrays(1,&g->array);
        {int p;for(p=0;p<OA_NPC_MAX;p++)if(g->people[p].program)oa_character_gpu_close(&g->people[p]);}oa_sky_close(&g->sky);if(g->foe.program)oa_character_gpu_close(&g->foe);oa_character_gpu_close(&g->character);opem_room_lighting_close(&g->room_lights);if(g->program)glDeleteProgram(g->program);
        eglMakeCurrent(g->display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);
        if(g->surface!=EGL_NO_SURFACE)eglDestroySurface(g->display,g->surface);
        if(g->context!=EGL_NO_CONTEXT)eglDestroyContext(g->display,g->context);
        eglTerminate(g->display);
    }
    memset(g,0,sizeof(*g));g->display=EGL_NO_DISPLAY;g->surface=EGL_NO_SURFACE;g->context=EGL_NO_CONTEXT;
}
/* Stress-test instrumentation, inert unless adb sets debug.opem.profile.
 * profile=1 logs, profile=2 also disables vsync; skip bits: 1 sky, 2 scene, 4 people, 8 UI; scale is a render scale percent. */
static struct{int on,skip,scale,crowd,shadow,walk,tour,far_m,tour_m,live,fx,heading;int fight;int slow;int64_t start,last,sim,submit,swap,worst;unsigned frames;GLuint query[8];unsigned qi;uint64_t gpu,gpu_max;unsigned gpu_n;int timer;}prof;
static float world_time(void);
static int64_t now_ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (int64_t)t.tv_sec*1000000000+t.tv_nsec;}
static int prop_int(const char *name,int fallback){char v[PROP_VALUE_MAX]={0};return __system_property_get(name,v)>0?atoi(v):fallback;}
static int prof_pulse;
static void prof_read(void){prof.on=prop_int("debug.opem.profile",0);prof.skip=prop_int("debug.opem.skip",0);prof.scale=prop_int("debug.opem.scale",100);prof.crowd=prop_int("debug.opem.crowd",1);prof.shadow=prop_int("debug.opem.shadow",0);prof.walk=prop_int("debug.opem.walk",0);prof.tour=prop_int("debug.opem.tour",0);prof.far_m=prop_int("debug.opem.far",1000);prof.tour_m=prop_int("debug.opem.tourr",320);stream_far=(float)prof.far_m*100.0f;prof.live=prop_int("debug.opem.live",255);prof.fx=prop_int("debug.opem.fx",0);prof.fight=prop_int("debug.opem.fight",0);prof.slow=prop_int("debug.opem.slow",0);prof.heading=prop_int("debug.opem.heading",0);{extern int oa_stream_hide,oa_stream_leaf_lod_override,oa_stream_leaf_native;oa_stream_hide=prop_int("debug.opem.hide",0);oa_stream_leaf_lod_override=prop_int("debug.opem.leaflod",-1);oa_stream_leaf_native=prop_int("debug.opem.leafnative",1);}prof_pulse=prop_int("debug.opem.pulse",0);}
static void prof_gl_start(void){const char *x=(const char*)glGetString(GL_EXTENSIONS);prof.timer=prof.on&&x&&strstr(x,"GL_EXT_disjoint_timer_query");if(prof.timer){glGenQueries(8,prof.query);prof.qi=0;}LOGI("Profile on=%d skip=%d scale=%d gpu_timer=%d renderer=%s",prof.on,prof.skip,prof.scale,prof.timer,(const char*)glGetString(GL_RENDERER));}
static int graphics_open(graphics *g,ANativeWindow *window,const amalur_scene_mesh *mesh,const scene_materials_v09 *materials,const oa_character *character,const oa_npcs *npcs,const oa_character *foe,const uint8_t *sky_bytes,size_t sky_size,int outdoor){
    EGLConfig config;EGLint configurations=0,format=0;
    const EGLint attributes[]={EGL_SURFACE_TYPE,EGL_WINDOW_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES3_BIT,
        EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_DEPTH_SIZE,24,EGL_NONE};
    const EGLint context_attributes[]={EGL_CONTEXT_CLIENT_VERSION,3,EGL_NONE};
    g->display=eglGetDisplay(EGL_DEFAULT_DISPLAY);
    if(g->display==EGL_NO_DISPLAY || !eglInitialize(g->display,NULL,NULL))goto fail;
    if(!eglBindAPI(EGL_OPENGL_ES_API) || !eglChooseConfig(g->display,attributes,&config,1,&configurations) || !configurations)goto fail;
    if(!eglGetConfigAttrib(g->display,config,EGL_NATIVE_VISUAL_ID,&format)||ANativeWindow_setBuffersGeometry(window,0,0,format)!=0)goto fail;
    /* Always scale physical defaults, not the previous room's scaled buffer. */
    {int full_w=ANativeWindow_getWidth(window),full_h=ANativeWindow_getHeight(window);int scale=prof.scale<25?25:prof.scale>100?100:prof.scale;int render_w=full_w*scale/100,render_h=full_h*scale/100;if(scale!=100&&ANativeWindow_setBuffersGeometry(window,render_w,render_h,format)!=0)goto fail;LOGI("Render scale requested=%d applied=%d physical=%dx%d selected=%dx%d",prof.scale,scale,full_w,full_h,render_w,render_h);}
    g->surface=eglCreateWindowSurface(g->display,config,window,NULL);
    if(g->surface==EGL_NO_SURFACE)goto fail;
    g->context=eglCreateContext(g->display,config,EGL_NO_CONTEXT,context_attributes);
    if(g->context==EGL_NO_CONTEXT || !eglMakeCurrent(g->display,g->surface,g->surface,g->context))goto fail;
    eglSwapInterval(g->display,prof.on==2?0:1);prof_gl_start();
    glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LEQUAL);glDisable(GL_CULL_FACE);
    if(mesh->vertices||active_stream){
        g->program=program_create();if(!g->program)goto fail;
        g->matrix_location=glGetUniformLocation(g->program,"mvp");
        g->has_texture_location=glGetUniformLocation(g->program,"has_texture");g->sampler_location=glGetUniformLocation(g->program,"base_texture");
        if(!opem_room_lighting_open(&g->room_lights,g->program,outdoor)){LOGE("Room light uniforms unavailable");goto fail;}
        LOGI("Room lighting source records=36 %s shader_equation=recovered_cube_shadow_sun_point native_parity=0",opem_room_lighting_identity());
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
    if(character->ready){if(oa_character_gpu_open(&g->character,character,outdoor))LOGI("Character GPU ready parts=%u textures=%u clips=%u",character->part_count,character->texture_count,character->clip_count);else LOGE("Character unavailable; continuing without it");}
    if(outdoor&&sky_bytes&&!oa_sky_open(&g->sky,sky_bytes,sky_size))LOGE("Sky unavailable; flat color remains");
    if(foe->ready&&!oa_character_gpu_open(&g->foe,foe,outdoor))LOGE("Enemy unavailable");
    {unsigned p;for(p=0;p<npcs->count;p++)if(!oa_character_gpu_open(&g->people[p],npcs->people+p,outdoor))LOGE("Person %u unavailable",p);}
    if(active_stream){EGLint sw=0,sh=0;eglQuerySurface(g->display,g->surface,EGL_WIDTH,&sw);eglQuerySurface(g->display,g->surface,EGL_HEIGHT,&sh);{int wi,all=1;for(wi=0;wi<7;wi++){g->world_programs[wi]=oa_world_program(wi,OA_LIVE_LIGHTS);all=all&&g->world_programs[wi];}if(all&&oa_lightgrid_open(&g->light_grid,oa_live_lights,OA_LIVE_LIGHTS)){g->world_program=g->world_programs[0];LOGI("LIGHT GRID lights=%d tile_refs=%u dropped=%u size=%dx%d",OA_LIVE_LIGHTS,g->light_grid.references,g->light_grid.dropped,g->light_grid.width,g->light_grid.height);}else LOGE("World shader unavailable");}oa_post_open(&g->post,sw,sh);oa_native_shadow_open(&g->native_shadow,1024);if(oa_native_sky_open_assets(&g->native_sky,fx_manager,"world/native-sky-lower.oatx","world/native-sky-upper.oatx"))LOGI("Native sky resources ready");if(oa_native_water_open(&g->native_water,fx_manager,"world/water-native.bin"))LOGI("Native river resources ready");}
    if(!exploration_overlay_open(&g->overlay)){LOGE("Exploration overlay initialization failed");goto fail;}
    if(!ui_bytes||!oa_ui_open(&g->ui,ui_bytes,ui_size))LOGE("Veil UI unavailable");
    g->ready=1;LOGI("GLES scene surface ready; imported vertices=%u",mesh->vertex_count);return 1;
fail:LOGE("EGL/GLES initialization failed; EGL error=0x%x",eglGetError());graphics_close(g);return 0;
}
enum{OA_REAGENT_ROWS=96};
/* Symbols are engine identifiers; shows them in words until they are matched to the game's text. */
static void reagent_display(const char *symbol,char *out,size_t cap){size_t i=0;int start=1;const char *s=symbol;if(!strncmp(s,"reagentsource_",14))s+=14;else if(!strncmp(s,"reagent_",8))s+=8;
    for(;*s&&i+1<cap;s++){char c=*s=='_'?' ':*s;if(c==' '){start=1;out[i++]=c;continue;}out[i++]=start?(char)toupper((unsigned char)c):c;start=0;}out[i]=0;}
static oa_native_wind native_wind;static int native_wind_ready,reference_wind_ready;static float native_wind_values[64][4],reference_wind_values[64][4],native_leaf_values[12];static double native_scene_time;
static float world_time(void){
#ifdef OA_DESKTOP
if(oa_desktop_reference_active())return 75.51799774169922f;
#endif
return (float)native_scene_time;}
static void world_wind_update(float dt){native_scene_time+=dt;oa_native_leaf_palette((uint32_t)monotonic_ms(),native_leaf_values);
#ifdef OA_DESKTOP
if(oa_desktop_reference_active())oa_native_leaf_palette(305493984u,native_leaf_values);
#endif
if(!native_wind_ready){oa_native_wind_init(&native_wind);native_wind_ready=1;}if(dt>0)oa_native_wind_step(&native_wind,(uint32_t)(dt*1000.f+.5f));oa_native_wind_palette(&native_wind,native_wind_values);
#ifdef OA_DESKTOP
 if(oa_desktop_reference_active()&&!reference_wind_ready){AAsset *a=AAssetManager_open(fx_manager,"world/wind.bin",AASSET_MODE_BUFFER);if(a){if(AAsset_getLength(a)==1024&&AAsset_read(a,reference_wind_values,1024)==1024)reference_wind_ready=1;AAsset_close(a);}}
 if(oa_desktop_reference_active()&&reference_wind_ready)memcpy(native_wind_values,reference_wind_values,1024);
#endif
}
#ifdef OA_DESKTOP
static int oa_probe_capture,oa_probe_mode;
void oa_desktop_material_probe_stage(GLuint fbo,int width,int height,const char *stage){
    static const int xy[3][2]={{800,150},{980,210},{500,35}};GLint kept;int j;
    if(!oa_probe_capture)return;glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING,&kept);glBindFramebuffer(GL_READ_FRAMEBUFFER,fbo);
    for(j=0;j<3;j++){unsigned char rgba[4]={0};int x=xy[j][0]*width/1536,y=height-1-xy[j][1]*height/864;glReadPixels(x,y,1,1,GL_RGBA,GL_UNSIGNED_BYTE,rgba);LOGI("MaterialProbe mode=%d stage=%s pixel=%d,%d rgba=%u,%u,%u,%u error=%x",oa_probe_mode,stage,xy[j][0],xy[j][1],rgba[0],rgba[1],rgba[2],rgba[3],glGetError());}
    if(!strcmp(stage,"DOF-fuzz-nearest")){unsigned char q[16]={0};int x=800*width/1536,y=height-1-150*height/864;glReadPixels(x-1,y,2,2,GL_RGBA,GL_UNSIGNED_BYTE,q);LOGI("MaterialProbe mode=%d stage=DOF-fuzz-quad pixel=800,150 coc_TL_TR_BL_BR=%u,%u,%u,%u depth_TL_TR_BL_BR=%u,%u,%u,%u error=%x",oa_probe_mode,q[8],q[12],q[0],q[4],q[9],q[13],q[1],q[5],glGetError());}
    glBindFramebuffer(GL_READ_FRAMEBUFFER,(GLuint)kept);
}
void oa_desktop_material_probe_texture(GLuint tex,int width,int height,const char *stage){
    GLuint fbo;GLint read,draw;if(!oa_probe_capture||!tex)return;glGetIntegerv(GL_READ_FRAMEBUFFER_BINDING,&read);glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING,&draw);glGenFramebuffers(1,&fbo);glBindFramebuffer(GL_FRAMEBUFFER,fbo);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,tex,0);
    if(glCheckFramebufferStatus(GL_FRAMEBUFFER)==GL_FRAMEBUFFER_COMPLETE)oa_desktop_material_probe_stage(fbo,width,height,stage);else LOGE("MaterialProbe incomplete texture=%u",tex);
    glBindFramebuffer(GL_READ_FRAMEBUFFER,(GLuint)read);glBindFramebuffer(GL_DRAW_FRAMEBUFFER,(GLuint)draw);glDeleteFramebuffers(1,&fbo);
}
#endif
/* Sets the outdoor material shader up, chooses the nearest real lights, and draws the streamed world. */
static void world_draw(graphics *g,const float mvp[16],const float eye[3],int shadow_on,const float shadow_matrix[16],int first_phase,int last_phase,int depth_only){
    const float *sun=opem_town_sun(),*sc=opem_town_sun_rgb(),*sh=opem_town_shadow_rgba();int v,i;
    for(v=0;v<7;v++){GLuint w=g->world_programs[v];glUseProgram(w);glUniformMatrix4fv(glGetUniformLocation(w,"mvp"),1,GL_FALSE,mvp);glUniform3fv(glGetUniformLocation(w,"eye"),1,eye);glUniform3fv(glGetUniformLocation(w,"sun_color"),1,sc);glUniform3fv(glGetUniformLocation(w,"sun_dir"),1,sun);glUniform3fv(glGetUniformLocation(w,"shadow_color"),1,sh);glUniform3fv(glGetUniformLocation(w,"fog_color"),1,oa_live_fog_color);/* The game's fog constants. */glUniform2f(glGetUniformLocation(w,"fog"),oa_live_fog_density/500000.f,oa_live_fog_start);glUniform1i(glGetUniformLocation(w,"features"),prof.live);
#ifdef OA_DESKTOP
        {char probe[PROP_VALUE_MAX]={0};__system_property_get("debug.opem.materialprobe",probe);glUniform1i(glGetUniformLocation(w,"oa_probe"),depth_only?0:atoi(probe));}
#endif
glUniform1i(glGetUniformLocation(w,"depth_only"),depth_only);glUniform1i(glGetUniformLocation(w,"native_ao_on"),!depth_only&&g->post.ao_current!=0);glUniform1i(glGetUniformLocation(w,"ambient_occlusion"),13);glUniform4fv(glGetUniformLocation(w,"wind_palette[0]"),64,&native_wind_values[0][0]);glUniform1fv(glGetUniformLocation(w,"leaf_palette[0]"),12,native_leaf_values);glUniform1i(glGetUniformLocation(w,"shadow_on"),shadow_on);glUniform1f(glGetUniformLocation(w,"game_time"),world_time());
        {static const char *names[8]={"t0","t1","t2","t3","t4","t5","t6","t7"};for(i=0;i<8;i++)glUniform1i(glGetUniformLocation(w,names[i]),i);}
        glUniform1i(glGetUniformLocation(w,"cube"),8);glUniform1i(glGetUniformLocation(w,"shadow_map"),9);glUniform1i(glGetUniformLocation(w,"light_grid"),10);glUniform3f(glGetUniformLocation(w,"grid"),g->light_grid.origin[0],g->light_grid.origin[1],g->light_grid.scale);glUniform2i(glGetUniformLocation(w,"grid_size"),g->light_grid.width,g->light_grid.height);
        if(shadow_on)glUniformMatrix4fv(glGetUniformLocation(w,"shadow_matrix"),1,GL_FALSE,shadow_matrix);}
    glActiveTexture(GL_TEXTURE8);glBindTexture(GL_TEXTURE_CUBE_MAP,g->room_lights.cube);
    if(shadow_on){glActiveTexture(GL_TEXTURE9);glBindTexture(GL_TEXTURE_2D,g->shadow_tex);}
    glActiveTexture(GL_TEXTURE10);glBindTexture(GL_TEXTURE_2D,g->light_grid.tex);glBindBufferBase(GL_UNIFORM_BUFFER,0,g->light_grid.ubo);
    glActiveTexture(GL_TEXTURE13);glBindTexture(GL_TEXTURE_2D,g->post.ao_current);
    oa_stream_draw_world_range(active_stream,mvp,g->world_programs,(unsigned)prof.live,first_phase,last_phase,first_phase==0);
    glActiveTexture(GL_TEXTURE0);
}
static int graphics_draw(graphics *g,const amalur_scene_mesh *mesh,const scene_materials_v09 *materials,const camera *c,const exploration_input *input,const oa_interaction *interaction,int room_lighting,const char *door_prompt,oa_menu *menu,int world,float dt){
    float hud[3];EGLint width,height;int64_t prof_t0=now_ns();
    if(prof.timer){glBeginQuery(0x88BF,prof.query[prof.qi]);}
    {const oa_combat *f=&c->combat;float dx=c->foe.feet[0]-c->body.feet[0],dy=c->foe.feet[1]-c->body.feet[1];hud[0]=f->player_hp/f->player_max;hud[1]=f->foe!=OA_FOE_DEAD&&dx*dx+dy*dy<2200.f*2200.f?f->foe_hp/f->foe_max:-1.f;hud[2]=f->player_dead?1.f:0.f;}
    if(!eglQuerySurface(g->display,g->surface,EGL_WIDTH,&width) || !eglQuerySurface(g->display,g->surface,EGL_HEIGHT,&height))return 0;
    if(width<=0||height<=0)return 1;g->width=width;g->height=height;glViewport(0,0,width,height);
    if(g->room_lights.outdoor)glClearColor(.46f,.60f,.76f,1);else glClearColor(mesh->vertices?0.055f:0.17f,0.065f,0.08f,1);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
    if((mesh->vertices||active_stream)&&menu->screen!=OA_SCREEN_TITLE&&!(menu->screen==OA_SCREEN_OPTIONS&&menu->from==OA_SCREEN_TITLE)){float matrix[16],eye[3],shadow_matrix[16];int shadow_on=0;camera_matrix(c,(float)width/(float)height,matrix,eye);
#ifdef OA_DESKTOP
        oa_desktop_scene_state(world,c->body.feet,c->walk_yaw,c->walk_pitch,c->boom,matrix,eye,c->character.oneshot,c->combat.player_hp,c->body.grounded);
#endif

        world_wind_update(dt);if(active_stream)oa_stream_update(active_stream,eye);oa_actors_gpu_update(active_actors,&g->character);
        /* Sun shadow map around the player. Filtering and range are authored host choices. */
        if(active_stream&&!(prof.live&128)&&(prof.shadow||menu->settings.shadows)&&c->walking&&g->program){
            enum{SIZE=2048};const float *sun=opem_town_sun();float half=(float)(prof.shadow?prof.shadow:60)*100.0f,pos[3],side[3],up[3],zup[3]={0,0,1},fwd[3],view[16]={0},proj[16]={0},snap;int a;
            if(!g->shadow_fbo){glGenTextures(1,&g->shadow_tex);glBindTexture(GL_TEXTURE_2D,g->shadow_tex);glTexStorage2D(GL_TEXTURE_2D,1,GL_DEPTH_COMPONENT24,SIZE,SIZE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_COMPARE_MODE,GL_COMPARE_REF_TO_TEXTURE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_COMPARE_FUNC,GL_LEQUAL);glGenFramebuffers(1,&g->shadow_fbo);glBindFramebuffer(GL_FRAMEBUFFER,g->shadow_fbo);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_DEPTH_ATTACHMENT,GL_TEXTURE_2D,g->shadow_tex,0);{GLenum none=GL_NONE;glDrawBuffers(1,&none);}glReadBuffer(GL_NONE);if(glCheckFramebufferStatus(GL_FRAMEBUFFER)!=GL_FRAMEBUFFER_COMPLETE)LOGE("Shadow target incomplete");glBindTexture(GL_TEXTURE_2D,0);}
            snap=half*2.0f/SIZE;for(a=0;a<3;a++){pos[a]=roundf(c->body.feet[a]/snap)*snap+sun[a]*20000.0f;fwd[a]=-sun[a];}
            cross3(fwd,zup,side);normalize3(side);cross3(side,fwd,up);
            view[0]=side[0];view[4]=side[1];view[8]=side[2];view[12]=-dot3(side,pos);view[1]=up[0];view[5]=up[1];view[9]=up[2];view[13]=-dot3(up,pos);view[2]=-fwd[0];view[6]=-fwd[1];view[10]=-fwd[2];view[14]=dot3(fwd,pos);view[15]=1;
            proj[0]=proj[5]=1.0f/half;proj[10]=-2.0f/40000.0f;proj[14]=-1.0f;proj[15]=1;multiply4(shadow_matrix,proj,view);
            glBindFramebuffer(GL_FRAMEBUFFER,g->shadow_fbo);glViewport(0,0,SIZE,SIZE);glClear(GL_DEPTH_BUFFER_BIT);glEnable(GL_POLYGON_OFFSET_FILL);glPolygonOffset(2.0f,4.0f);
            glUseProgram(g->program);opem_room_lighting_upload(&g->room_lights,0);glUniform1i(glGetUniformLocation(g->program,"room_shadow_on"),0);glUniform1i(glGetUniformLocation(g->program,"room_shadow_map"),3);glUniformMatrix4fv(g->matrix_location,1,GL_FALSE,shadow_matrix);glUniform1f(glGetUniformLocation(g->program,"alpha_cut"),.5f);
            glUniform1i(g->sampler_location,0);oa_stream_draw(active_stream,shadow_matrix,g->has_texture_location,-1,c->body.feet,half*1.5f);
            if(c->collision_ready
#ifdef OA_DESKTOP
        &&!oa_desktop_reference_active()
#endif
        ){oa_character_gpu_draw(&g->character,&c->character,shadow_matrix,0,0.f);}if(c->foe_ready)oa_character_gpu_draw(&g->foe,&c->foe,shadow_matrix,0,.5f);oa_actors_draw_shadow(active_actors,shadow_matrix,c->body.feet);
            glDisable(GL_POLYGON_OFFSET_FILL);glBindFramebuffer(GL_FRAMEBUFFER,0);glViewport(0,0,width,height);shadow_on=1;}
        {int live_post=active_stream&&g->post.ready&&g->world_program;if(live_post){oa_post_begin(&g->post);glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LEQUAL);glDepthMask(GL_TRUE);glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE);glDisable(GL_CULL_FACE);glDisable(GL_BLEND);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);g->post.ao_current=0;
 if((prof.live&128)&&g->post.native_ao.ready){glColorMask(GL_FALSE,GL_FALSE,GL_FALSE,GL_FALSE);world_draw(g,matrix,eye,0,shadow_matrix,0,3,1);glDisable(GL_CULL_FACE);if(c->collision_ready
#ifdef OA_DESKTOP
 &&!oa_desktop_reference_active()
#endif
 ){oa_character_gpu_draw(&g->character,&c->character,matrix,0,0.f);}if(c->foe_ready&&!(prof.skip&4))oa_character_gpu_draw(&g->foe,&c->foe,matrix,0,.5f);if(!(prof.skip&4)){unsigned pi;oa_actors_draw_shadow(active_actors,matrix,c->body.feet);for(pi=0;pi<c->npcs.count;pi++)oa_character_gpu_draw(&g->people[pi],c->npcs.people+pi,matrix,0,.5f);}glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE);oa_post_make_ao(&g->post,matrix);
 if(g->native_shadow.ready&&(prof.shadow||menu->settings.shadows)&&oa_native_shadow_update(&g->native_shadow,matrix,eye,opem_town_sun(),NULL)){int ci;for(ci=2;ci>=0;ci--){oa_native_shadow_begin(&g->native_shadow,ci);glColorMask(GL_FALSE,GL_FALSE,GL_FALSE,GL_FALSE);world_draw(g,g->native_shadow.cascade[ci].vp,eye,0,shadow_matrix,0,3,1);glDisable(GL_CULL_FACE);if(c->collision_ready
#ifdef OA_DESKTOP
 &&!oa_desktop_reference_active()
#endif
 ){oa_character_gpu_draw(&g->character,&c->character,g->native_shadow.cascade[ci].vp,0,0.f);}if(c->foe_ready&&!(prof.skip&4))oa_character_gpu_draw(&g->foe,&c->foe,g->native_shadow.cascade[ci].vp,0,.5f);if(!(prof.skip&4)){unsigned pi;oa_actors_draw_shadow(active_actors,g->native_shadow.cascade[ci].vp,c->body.feet);for(pi=0;pi<c->npcs.count;pi++)oa_character_gpu_draw(&g->people[pi],c->npcs.people+pi,g->native_shadow.cascade[ci].vp,0,.5f);}glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE);oa_native_shadow_resolve(&g->native_shadow,ci,g->post.depth_tex,g->post.native_ao.fbo[2],g->post.w,g->post.h);}}
 glBindFramebuffer(GL_FRAMEBUFFER,g->post.scene_fbo);glViewport(0,0,g->post.w,g->post.h);glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LEQUAL);glDepthMask(GL_TRUE);glDisable(GL_BLEND);glDisable(GL_CULL_FACE);glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE);}}
        memcpy(oa_sky_below,oa_live_fog_color,sizeof(oa_sky_below));if((prof.live&128)&&!(prof.live&512)&&g->native_sky.ready&&!(prof.skip&1)){float sky_params[20];oa_native_sky_bridge_noon_parameters(sky_params,world_time());oa_native_sky_draw(&g->native_sky,matrix,sky_params);glDepthMask(GL_TRUE);glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LEQUAL);}else if(g->sky.ready&&!(prof.skip&1))oa_sky_draw(&g->sky,matrix,eye,fminf(c->radius*8.0f,stream_far*1.4f),world_time(),live_post?0:g->room_lights.lut);}
        glUseProgram(g->program);opem_room_lighting_upload(&g->room_lights,room_lighting);glUniformMatrix4fv(g->matrix_location,1,GL_FALSE,matrix);glUniform1f(glGetUniformLocation(g->program,"alpha_cut"),g->room_lights.outdoor?.5f:0.f);glUniform1i(glGetUniformLocation(g->program,"room_shadow_map"),3);glUniform1i(glGetUniformLocation(g->program,"room_shadow_on"),shadow_on);if(shadow_on){glUniformMatrix4fv(glGetUniformLocation(g->program,"room_shadow_matrix"),1,GL_FALSE,shadow_matrix);glActiveTexture(GL_TEXTURE3);glBindTexture(GL_TEXTURE_2D,g->shadow_tex);glActiveTexture(GL_TEXTURE0);}
        glBindVertexArray(g->array);
        if(prof.skip&2){}else if(active_stream&&g->world_program)world_draw(g,matrix,eye,shadow_on,shadow_matrix,0,3,0);else if(g->materials.ready&&!scene_material_renderer_v09_draw(&g->materials,materials,g->has_texture_location,g->sampler_location)){
            LOGE("Material drawing failed; reverting to diagnostic colors");scene_material_renderer_v09_close(&g->materials);glDisableVertexAttribArray(3);
        }
        if(!active_stream&&!g->materials.ready&&!(prof.skip&2)){glUniform1i(g->has_texture_location,0);glDrawArrays(GL_TRIANGLES,0,(GLsizei)mesh->vertex_count);}glBindVertexArray(0);
        if(c->collision_ready
#ifdef OA_DESKTOP
        &&!oa_desktop_reference_active()
#endif
        ){oa_character_gpu_draw(&g->character,&c->character,matrix,room_lighting,0.f);}
        if(c->foe_ready&&!(prof.skip&4))oa_character_gpu_draw(&g->foe,&c->foe,matrix,room_lighting,.5f);if(!(prof.skip&4))oa_actors_draw(active_actors,matrix,room_lighting);
        if(!(prof.skip&4)){unsigned p;int n;for(n=0;n<prof.crowd;n++)for(p=0;p<c->npcs.count;p++){oa_character *person=(oa_character*)(c->npcs.people+p);float kept[3];
            /* Crowd load: each extra person is posed on the CPU and placed around the player, as a live crowd would be. */
            if(n){float a=(float)(n*12+p)*2.399963f,r=350.f+(float)n*90.f;memcpy(kept,person->feet,sizeof(kept));person->feet[0]=c->body.feet[0]+cosf(a)*r;person->feet[1]=c->body.feet[1]+sinf(a)*r;person->feet[2]=c->body.feet[2];oa_character_pose(person);}
            oa_character_gpu_draw(&g->people[p],person,matrix,room_lighting,.5f);
            if(n){memcpy(person->feet,kept,sizeof(kept));oa_character_pose(person);}}}
#ifdef OA_DESKTOP
        if(active_stream&&g->post.ready&&oa_desktop_reference_active()){
            static int pending=-99,stable=0,recorded=-99;char text[PROP_VALUE_MAX]={0};int mode;
            __system_property_get("debug.opem.materialprobe",text);mode=atoi(text);
            if(pending!=mode){pending=mode;stable=0;}else stable++;
            oa_probe_capture=(stable>=8&&recorded!=mode);oa_probe_mode=mode;
            if(oa_probe_capture){recorded=mode;oa_desktop_material_probe_stage(g->post.scene_fbo,g->post.w,g->post.h,"opaque");if(g->post.ao_current)oa_desktop_material_probe_stage(g->post.native_ao.fbo[2],g->post.w,g->post.h,"AO");}
        }else oa_probe_capture=0;
#endif
        if(active_stream&&g->post.ready&&g->world_program){
 if((prof.live&128)&&!(prof.live&256)&&g->native_water.state){float block[32],cut;oa_native_water_environment env;memset(&env,0,sizeof(env));env.ambient_cube=g->room_lights.cube;memcpy(env.sun_direction,opem_town_sun(),12);memcpy(env.sun_color,opem_town_sun_rgb(),12);memcpy(env.shadow_color,opem_town_shadow_rgba(),12);env.water_fog[0]=80;env.water_fog[1]=.01f;env.water_fog[2]=1;
 if(oa_native_ao_parameters(block,&cut,matrix,g->post.w,g->post.h)&&oa_post_snapshot(&g->post)){float inv[2]={1.f/block[21],-block[20]/block[21]};if(oa_native_water_draw(&g->native_water,matrix,eye,g->post.opaque_color,g->post.opaque_depth,inv,world_time(),&env)){if(!g->native_observed){LOGI("Native fidelity rendered water_draws=8 ao=%u cascades=%d sky=%d features=%d",g->post.ao_current,g->native_shadow.ready,g->native_sky.ready,prof.live);g->native_observed=1;}}else if(g->native_observed>=0){LOGE("Native river draw failed");g->native_observed=-1;}}}
 
#ifdef OA_DESKTOP
  oa_desktop_material_probe_stage(g->post.scene_fbo,g->post.w,g->post.h,"water");
#endif
  glDisable(GL_CULL_FACE);world_draw(g,matrix,eye,shadow_on,shadow_matrix,4,6,0);
 if(prof.fx)oa_post_fx(&g->post,matrix,eye,c->body.feet,prof.fx,world_time());if(!active_fx&&!fx_tried&&fx_manager){fx_tried=1;active_fx=oa_fx_open(fx_manager);LOGI("FX %s",active_fx?"ready":"absent");}oa_fx_update(active_fx,eye,dt);oa_fx_draw(active_fx,matrix,oa_live_fog_color,oa_live_fog_density/500000.f,oa_live_fog_start);
            
#ifdef OA_DESKTOP
  oa_desktop_material_probe_stage(g->post.scene_fbo,g->post.w,g->post.h,"transparents");
#endif
  {float native_post[4];int native=(prof.live&64)&&oa_stream_native_post(active_stream,native_post);oa_post_end(&g->post,g->room_lights.lut,oa_live_bloom,oa_live_bloom_cut,2.0f,stream_far*1.6f,(prof.live&2)!=0,(prof.live&1)!=0,width,height,native?native_post:NULL,matrix);
#ifdef OA_DESKTOP
  oa_desktop_material_probe_stage(0,width,height,"final");
#endif
}}}
    if(interaction&&interaction->window_open)exploration_overlay_draw(&g->overlay,width,height,input,c->walking,c->collision_ready,interaction,room_lighting,door_prompt,NULL);
    else{oa_hud_view view;char hud_prop[PROP_VALUE_MAX]={0};const float *door=oa_doors[world];memset(&view,0,sizeof(view));
        view.health=hud[0];view.foe=c->foe_ready?hud[1]:-1.f;view.dead=hud[2]>0;view.health_now=c->combat.player_hp;view.health_max=c->combat.player_max;view.yaw=c->walk_yaw;view.feet_x=c->body.feet[0];view.feet_y=c->body.feet[1];view.target_x=door[0];view.target_y=door[1];view.has_target=1;view.room_lighting=room_lighting;{float focus_hp;const char *focus_name;if(oa_actors_focus(active_actors,c->body.feet,&focus_hp,&focus_name)){view.foe=focus_hp;view.foe_name=focus_name;}}
        view.location=world?OA_LIVE_AREA:"Alchemy Shop";view.zone=OA_LIVE_ZONE;view.prompt=view.dead?"You Have Fallen":interaction&&interaction->ready&&interaction->selected.generation?"Alchemy":door_prompt;
        view.move_active=input->move_id>=0;view.move_origin_x=input->move_origin_x;view.move_origin_y=input->move_origin_y;view.move_x=input->move_x;view.move_y=input->move_y;
        /* Test aid: adb shell setprop debug.opem.hud off hides the HUD for clean captures. */
        {static oa_reagent_row rows[OA_REAGENT_ROWS];static char names[OA_REAGENT_ROWS][64];size_t i;int n=0;
         if(menu->screen==OA_SCREEN_INVENTORY&&interaction)for(i=0;i<interaction->catalog.reagent_count&&n<OA_REAGENT_ROWS;i++){uint32_t have=oa_inventory_count(&interaction->inventory,interaction->catalog.reagents[i].id);if(have){reagent_display(interaction->catalog.reagents[i].symbol,names[n],sizeof(names[n]));rows[n].name=names[n];rows[n].count=have;n++;}}
         view.reagents=rows;view.reagent_count=n;}
        view.show_hud=!(__system_property_get("debug.opem.hud",hud_prop)>0&&!strcmp(hud_prop,"off"));
        oa_ui_begin(&g->ui);if(g->ui.ready&&!(prof.skip&8))oa_menu_frame(menu,&g->ui,width,height,&view,dt);oa_ui_end(&g->ui,width,height);}
    {int64_t t1,t2;
     if(prof.timer){GLuint ready=0,ns=0,q;GLint disjoint=0;glEndQuery(0x88BF);prof.qi=(prof.qi+1)%8;q=prof.query[prof.qi];glGetQueryObjectuiv(q,GL_QUERY_RESULT_AVAILABLE,&ready);glGetIntegerv(0x8FBB,&disjoint);if(ready&&!disjoint){glGetQueryObjectuiv(q,GL_QUERY_RESULT,&ns);if(ns&&ns<1000000000u){prof.gpu+=ns;prof.gpu_n++;if(ns>prof.gpu_max)prof.gpu_max=ns;}}{GLenum e=glGetError();static int told;if(e!=GL_NO_ERROR&&!told){told=1;LOGE("Profiler left GL error 0x%x",e);}}}
     t1=now_ns();
     if(!eglSwapBuffers(g->display,g->surface)){LOGE("EGL swap failed:0x%x",eglGetError());return 0;}
     t2=now_ns();
     if(prof.on&&active_stream&&prof.frames==239){oa_stream_stats st;oa_stream_get_stats(active_stream,&st);LOGI("STREAM cells=%u/%u draws=%u tris=%u gpu_mb=%.0f cpu_mb=%.0f textures=%u queued=%u update_worst_ms=%.2f native_material_draws=%u native_terrain_draws=%u features=%d forced_leaf_cells=%u native_leaf_cells=%u",st.cells_drawn,st.cells,st.draws,st.triangles,st.gpu_mb,st.cpu_mb,st.textures,st.queued,st.upload_worst_ms,st.native_material_draws,st.native_terrain_draws,prof.live,st.forced_leaf_cells,st.native_leaf_cells);}
     if(prof.on&&prof.last&&t2-prof.last>40000000){LOGI("HITCH gap_ms=%.1f sim_ms=%.1f submit_ms=%.1f swap_ms=%.1f",(t2-prof.last)/1e6,(prof_t0-prof.start)/1e6,(t1-prof_t0)/1e6,(t2-t1)/1e6);}
      if(prof.on&&prof.tour&&prof.frames==239)LOGI("TOUR frames=%u airborne=%u reached=%u gave_up=%u detours=%u feet=(%.0f %.0f %.0f)",tour_frames,tour_air,tour_reached,tour_gave_up,tour_detours,c->body.feet[0],c->body.feet[1],c->body.feet[2]);if(prof.on&&active_actors&&prof.frames==239){oa_actors_stats as;oa_audio_stats audio_now;oa_actors_get_stats(active_actors,&as);oa_audio_get_stats(active_audio,&audio_now);LOGI("ACTORS total=%u near=%u moving=%u chasing=%u bodies=%u drawn=%u models=%u rays=%u capsules=%u paths=%u update_ms=%.2f audio_voices=%u audio_mix_ms=%.3f audio_xruns=%u",as.total,as.near_count,as.moving,as.chasing,as.slots,as.drawn,as.models,as.rays,as.capsules,as.paths,as.update_ms,audio_now.voices,audio_now.mix_ms,audio_now.underruns);}
      if(prof.on){int64_t gap=prof.last?t2-prof.last:0;prof.last=t2;prof.sim+=prof_t0-prof.start;prof.submit+=t1-prof_t0;prof.swap+=t2-t1;if(gap>prof.worst)prof.worst=gap;
      if(++prof.frames==240){LOGI("PROFILE interval_ms=%.2f worst_ms=%.2f sim_ms=%.2f submit_ms=%.2f swap_ms=%.2f gpu_ms=%.2f gpu_max_ms=%.2f gpu_samples=%u size=%dx%d vertices=%u",(double)(t2-prof.start+prof.sim*0)/1e6*0+(prof.sim+prof.submit+prof.swap)/240.0/1e6,(double)prof.worst/1e6,prof.sim/240.0/1e6,prof.submit/240.0/1e6,prof.swap/240.0/1e6,prof.gpu_n?(double)prof.gpu/prof.gpu_n/1e6:-1.0,(double)prof.gpu_max/1e6,prof.gpu_n,width,height,mesh->vertex_count);prof.frames=0;prof.sim=prof.submit=prof.swap=prof.worst=0;prof.gpu=prof.gpu_max=0;prof.gpu_n=0;}}}
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
static void character_load(AAssetManager *manager,oa_character *character){
    AAsset *asset=AAssetManager_open(manager,"character.bin",AASSET_MODE_BUFFER);uint8_t *bytes;off_t size;char error[128];
    if(!asset){LOGE("Character asset missing");return;}
    size=AAsset_getLength(asset);bytes=size>0?(uint8_t*)malloc((size_t)size):NULL;
    if(bytes&&AAsset_read(asset,bytes,(size_t)size)==size&&oa_character_parse(character,bytes,(size_t)size,error,sizeof(error)))LOGI("Character asset loaded bytes=%lld joints=%u",(long long)size,character->joints);
    else{LOGE("Character asset rejected: %s",bytes?error:"allocation");free(bytes);}
    AAsset_close(asset);
}
static void materials_load(AAssetManager *manager,const amalur_scene_mesh *mesh,scene_materials_v09 *materials,const char *asset_name,const char *hex){
   unsigned char digest[32],*bytes=NULL;AAsset *asset=NULL;
    off64_t size;size_t offset=0;int i;char error[256];
    if(strlen(hex)!=64){LOGI("Materials disabled: no compiled scene identity; diagnostic colors");return;}
    for(i=0;i<32;++i){unsigned v;if(sscanf(hex+i*2,"%2x",&v)!=1){LOGE("Compiled scene identity invalid");return;}digest[i]=(unsigned char)v;}
    asset=AAssetManager_open(manager,asset_name,AASSET_MODE_STREAMING);
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
    const float *hint=c->spawn_hint?c->spawn_hint:oa_workbench_spawn_hint;char error[256];
    c->request_right=c->request_forward=0;
    if(c->world&&opem_controller_spawn(c->world,&c->body_config,hint,&c->body,error,sizeof(error))){
        c->collision_ready=1;c->walking=1;c->walk_yaw=1.5707963268f;c->walk_pitch=-.2f;c->boom=OA_CAMERA_BOOM;c->character.facing=c->walk_yaw;memcpy(c->character.feet,c->body.feet,sizeof(c->body.feet));
        LOGI("Exploration spawn validated feet=(%.2f %.2f %.2f) radius=%.1f height=%.1f new_host_controller=1",c->body.feet[0],c->body.feet[1],c->body.feet[2],c->body_config.radius,c->body_config.height);
    }else{c->collision_ready=0;c->walking=0;LOGE("Exploration movement unavailable: %s",c->world?error:"collision world absent");}
    exploration_pose_log(c,"reset",1);
}
static void character_update(camera *c,float right,float forward,float dt){
    float speed=sqrtf(right*right+forward*forward),pivot[3],back[3],hit=0,want=OA_CAMERA_BOOM,lean_rate=0;
    if(speed>1)speed=1;
    if(speed>.05f){float vx=cosf(c->walk_yaw)*forward+sinf(c->walk_yaw)*right,vy=sinf(c->walk_yaw)*forward-cosf(c->walk_yaw)*right,target=atan2f(vy,vx),turn=remainderf(target-c->character.facing,6.283185307f),before=c->character.facing;
        c->character.move_target=target;c->character.facing=remainderf(c->character.facing+oa_character_turn_step(&c->character,turn,dt),6.283185307f);lean_rate=remainderf(c->character.facing-before,6.283185307f)/(dt>.0001f?dt:.0001f);}
    /* How hard the slope and lean poses apply. The full-strength slope of 0.6 and turn of 6 radians a second are authored; both fade in over a fifth of a second. */
    {float dx=c->body.feet[0]-c->character.feet[0],dy=c->body.feet[1]-c->character.feet[1],run=sqrtf(dx*dx+dy*dy),want_slope=run>.5f&&speed>=.7f?clampf((c->body.feet[2]-c->character.feet[2])/run/.6f,-1.f,1.f):0.f,want_lean=speed>=.7f?clampf(lean_rate/6.f,-1.f,1.f):0.f,ease=dt*5.f>1.f?1.f:dt*5.f;c->character.slope+=(want_slope-c->character.slope)*ease;c->character.lean+=(want_lean-c->character.lean)*ease;if(fabsf(c->character.slope)<.01f)c->character.slope=0;if(fabsf(c->character.lean)<.01f)c->character.lean=0;}
    memcpy(c->character.feet,c->body.feet,sizeof(c->body.feet));
    oa_character_animate(&c->character,speed,speed*c->body_config.max_speed,dt);oa_character_pose(&c->character);
    pivot[0]=c->body.feet[0];pivot[1]=c->body.feet[1];pivot[2]=c->body.feet[2]+OA_CAMERA_PIVOT;
    back[0]=-cosf(c->walk_pitch)*cosf(c->walk_yaw);back[1]=-cosf(c->walk_pitch)*sinf(c->walk_yaw);back[2]=-sinf(c->walk_pitch);
    if(opem_collision_ray(c->world,pivot,back,OA_CAMERA_BOOM,&hit)&&hit<OA_CAMERA_BOOM)want=hit-12.0f;
    if(want<25.0f)want=25.0f;
    c->boom=want<c->boom?want:c->boom+(want-c->boom)*(dt*4.0f>1?1:dt*4.0f);
}
static void exploration_update(camera *c,exploration_input *input,float dt){
    float right,forward,yaw,pitch;char error[256];
    if(input->reset_requested){input->reset_requested=0;exploration_reset(c);exploration_input_clear(input);}
    if(input->toggle_requested){input->toggle_requested=0;c->walking=c->collision_ready&&!c->walking;exploration_input_clear(input);LOGI("Exploration view=%s",c->walking?"walk":"overview");c->request_right=c->request_forward=0;exploration_pose_log(c,"view",1);}
    exploration_input_axes(input,&right,&forward,&yaw,&pitch);
    c->request_right=right;c->request_forward=forward;
    if(c->walking&&c->collision_ready){
        c->walk_yaw=remainderf(c->walk_yaw-(input->look_dx+yaw*dt)*c->look_speed,6.283185307f);
        c->walk_pitch=clampf(c->walk_pitch+(pitch*dt-input->look_dy)*c->look_speed*(c->invert_look?-1.f:1.f),-1.45f,1.45f);
        if(!opem_controller_step(c->world,&c->body_config,&c->body,
            (cosf(c->walk_yaw)*forward+sinf(c->walk_yaw)*right)*c->body_config.max_speed*c->move_scale,
            (sinf(c->walk_yaw)*forward-cosf(c->walk_yaw)*right)*c->body_config.max_speed*c->move_scale,dt,error,sizeof(error))){
            /* Controller guarantees atomic freeze. Keep the safe view, disable
             * further walking until Reset successfully revalidates a spawn. */
            {char retry[256];opem_controller safe;LOGE("Exploration collision step stopped: %s feet=(%.0f %.0f %.0f)",error,c->body.feet[0],c->body.feet[1],c->body.feet[2]);
                /* Rough terrain can fail validation. Stand again at the last safe spot rather than ending control. */
                if(opem_controller_spawn(c->world,&c->body_config,c->body.last_safe_feet,&safe,retry,sizeof(retry))){c->body=safe;}
                else{c->collision_ready=0;c->walking=0;exploration_input_clear(input);LOGE("Exploration recovery failed: %s",retry);exploration_pose_log(c,"step_failure",1);}}
        }else if(c->body.recovered_last_step)++c->recovery_count;
        if(c->collision_ready)character_update(c,right*c->move_scale,forward*c->move_scale,dt);
    }else{
        c->yaw=remainderf(c->yaw-input->look_dx-yaw*dt,6.283185307f);
        c->pitch=clampf(c->pitch+input->look_dy-pitch*dt,-1.4f,1.4f);
        c->distance=clampf(c->distance*expf(-forward*dt),c->radius*.05f,c->radius*40);
    }
    input->look_dx=input->look_dy=0;
    exploration_pose_log(c,"changed",0);
}
static void input_drain(AInputQueue *queue,exploration_input *input,const graphics *g,int enabled,oa_interaction *interaction,const char *inventory_path,oa_menu *menu){
    AInputEvent *event;unsigned processed=0;
    while(queue&&processed++<256&&AInputQueue_getEvent(queue,&event)>=0){
        int handled=0;if(AInputQueue_preDispatchEvent(queue,event))continue;
        if(enabled){if(interaction->window_open){handled=oa_android_modal_event(interaction,event,g->width,g->height,inventory_path);exploration_input_clear(input);}else{handled=oa_menu_event(menu,event,g->width,g->height,input);if(!handled&&menu->screen==OA_SCREEN_GAME)handled=exploration_input_event(input,event,g->width,g->height);}}
        AInputQueue_finishEvent(queue,event,handled);
    }
}
/* Replaces scene, materials and collision. The caller reopens graphics afterwards. */
static void world_load(AAssetManager *manager,int world,amalur_scene_mesh *mesh,scene_materials_v09 *materials,camera *c){
    const float *arrive=c->spawn_hint;char error[256]="mesh load failed";opem_collision_stats stats;amalur_scene_mesh collision={0};
    oa_actors_close(active_actors);active_actors=NULL;oa_stream_close(active_stream);active_stream=NULL;
    amalur_scene_mesh_clear(mesh);scene_materials_v09_free(materials);memset(materials,0,sizeof(*materials));opem_collision_destroy(c->world);c->world=NULL;c->collision_ready=0;c->walking=0;
    if(world){active_stream=oa_stream_open(manager);active_actors=oa_actors_open(manager);oa_fx_close(active_fx);active_fx=NULL;fx_tried=0;fx_manager=manager;if(!active_audio)active_audio=oa_audio_open(manager);oa_actors_use_audio(active_actors,active_audio);snd_foot=oa_audio_group(active_audio,"foot_grass");snd_use=oa_audio_group(active_audio,"blade_use");snd_hit=oa_audio_group(active_audio,"blade_hit");snd_die=oa_audio_group(active_audio,"player_die");{static int bed;if(!bed){bed=1;oa_audio_loop(active_audio,oa_audio_group(active_audio,"bed_forest"),6.f);}}}
    if(active_stream)oa_stream_set_far(active_stream,stream_far);
    if(active_stream){const float *from=arrive?arrive:oa_doors[1];oa_stream_bounds(active_stream,c->center,&c->radius);c->distance=c->radius*2.5f;
        c->world=oa_stream_collision_now(active_stream,from,error,sizeof(error));
        if(c->world){opem_collision_get_stats(c->world,&stats);LOGI("World %d streamed collision triangles=%u",world,stats.triangles);c->spawn_hint=arrive;exploration_reset(c);}else LOGE("World %d collision unavailable: %s",world,error);}
    else{
    if(!mesh_load(manager,world?"town_scene.bin":"scene.bin",mesh)){LOGE("World %d scene unavailable",world);return;}
    {double radius2=0;int i;for(i=0;i<3;i++){double d=(double)mesh->bounds_max[i]-mesh->bounds_min[i];c->center[i]=(float)(((double)mesh->bounds_min[i]+mesh->bounds_max[i])*0.5);radius2+=d*d;}c->radius=(float)(sqrt(radius2)*0.5);c->distance=c->radius*2.5f;}
    if(mesh_load(manager,world?"town_collision.bin":"collision.bin",&collision)&&opem_collision_create(&c->world,collision.vertices,collision.vertex_count,9,error,sizeof(error))){opem_collision_get_stats(c->world,&stats);LOGI("World %d collision triangles=%u",world,stats.triangles);c->spawn_hint=arrive;exploration_reset(c);}
    else LOGE("World %d collision unavailable: %s",world,error);
    amalur_scene_mesh_clear(&collision);
    materials_load(manager,mesh,materials,world?"town_materials.bin":"scene_materials.bin",world?AMALUR_TOWN_SHA256:AMALUR_SCENE_SHA256);
    }
    oa_npcs_free(&c->npcs);
    free(c->sky_bytes);c->sky_bytes=NULL;c->sky_size=0;
    if(world){AAsset *asset=AAssetManager_open(manager,"town_sky.bin",AASSET_MODE_BUFFER);
        if(asset){size_t size=(size_t)AAsset_getLength64(asset);uint8_t *bytes=(uint8_t*)malloc(size);if(bytes&&AAsset_read(asset,bytes,size)==(int)size){c->sky_bytes=bytes;c->sky_size=size;}else free(bytes);AAsset_close(asset);}
        else LOGE("Sky asset missing");}
    if(c->foe.bytes)oa_character_free(&c->foe);
    c->foe_ready=0;c->move_scale=1;oa_combat_reset(&c->combat);oa_character_stop(&c->character);
    if(world&&c->world&&!active_stream){AAsset *asset=AAssetManager_open(manager,"town_enemy.bin",AASSET_MODE_BUFFER);
        if(asset){size_t size=(size_t)AAsset_getLength64(asset);uint8_t *bytes=(uint8_t*)malloc(size);const float place[3]={OA_FOE_SPAWN_X,OA_FOE_SPAWN_Y,OA_LIVE_START_Z+17.9f};
            if(bytes&&AAsset_read(asset,bytes,size)==(int)size&&oa_character_parse(&c->foe,bytes,size,error,sizeof(error))){
                if(opem_controller_spawn(c->world,&c->body_config,place,&c->foe_body,error,sizeof(error))){memcpy(c->foe.feet,c->foe_body.feet,sizeof(c->foe.feet));oa_character_pose(&c->foe);c->foe_ready=1;LOGI("Enemy ready at (%.0f %.0f %.0f)",c->foe.feet[0],c->foe.feet[1],c->foe.feet[2]);}
                else LOGE("Enemy spawn rejected: %s",error);}
            else{LOGE("Enemy rejected: %s",bytes?error:"allocation");free(bytes);}
            AAsset_close(asset);}}
    if(world&&!active_stream){AAsset *asset=AAssetManager_open(manager,"town_npcs.bin",AASSET_MODE_BUFFER);
        if(asset){const uint8_t *bytes=(const uint8_t*)AAsset_getBuffer(asset);size_t size=(size_t)AAsset_getLength64(asset);
            if(bytes&&oa_npcs_parse(&c->npcs,bytes,size,error,sizeof(error)))LOGI("Townspeople loaded count=%u",c->npcs.count);else LOGE("Townspeople rejected: %s",bytes?error:"no buffer");AAsset_close(asset);}
        else LOGE("Townspeople asset missing");}
    LOGI("World switched to %s ready=%d vertices=%u draws=%u textures=%u",world?"gorhart":"shop",c->collision_ready,mesh->vertex_count,materials->draw_count,materials->texture_count);
}
static void frame_rate_apply(ANativeWindow *window,int rate){
    /* API 30 and later; older systems keep their default. */
    typedef int32_t (*set_rate)(ANativeWindow*,float,int8_t);static set_rate call;static int looked;
    if(!looked){void *lib=dlopen("libandroid.so",RTLD_NOW);looked=1;if(lib)call=(set_rate)dlsym(lib,"ANativeWindow_setFrameRate");}
    if(call&&window){int32_t r=call(window,(float)rate,0);LOGI("Frame rate request %d Hz result=%d",rate,r);}
}
static void *worker_main(void *argument){
    activity_state *s=(activity_state*)argument;amalur_scene_mesh mesh={0};graphics g={0};camera c={0};unsigned epoch=0,input_epoch=0;int stop,resumed,focused;
    int world=0,world_request=-1;const char *door_prompt=NULL;
    static oa_menu menu;static oa_save loaded;int pending_load=0,applied_rate=-1,foe_down=0;ANativeWindow *rate_window=NULL;float last_dt=0;
    input_host inputs={0};amalur_runtime *realm=NULL;exploration_input movement;scene_materials_v09 materials={0};
    unsigned clear_epoch=0,inventory_changes=0;int64_t last_frame_ms=0;oa_interaction interaction={0};char inventory_path[1024];int room_lighting=1;int observed_lighting_mode=-1;unsigned lighting_frames=0;int64_t lighting_started_ms=0;
    prof_read();
    snprintf(inventory_path,sizeof(inventory_path),"%s/%s",s->activity->internalDataPath,"opem-inventory-v1.bin");
    exploration_input_clear(&movement);opem_controller_config_default(&c.body_config);c.move_scale=1;c.look_speed=1;oa_combat_reset(&c.combat);
    oa_menu_init(&menu,s->activity->internalDataPath,0);
    {AAsset *asset=AAssetManager_open(s->activity->assetManager,"oa_ui.bin",AASSET_MODE_BUFFER);if(asset){size_t size=(size_t)AAsset_getLength64(asset);uint8_t *bytes=(uint8_t*)malloc(size);if(bytes&&AAsset_read(asset,bytes,size)==(int)size){ui_bytes=bytes;ui_size=size;}else free(bytes);AAsset_close(asset);}else LOGE("UI asset missing");}
    /* Authored Workbench-area spawn: this selected indoor floor has no
     * corroborated overhead collision surface. Ground/contact and standing
     * capsule clearance remain mandatory; a missing ceiling is not a wall. */
    c.body_config.require_ceiling=0;
    /* Authored third-person run speed, matched to the run clip; not a recovered native value. */
    c.body_config.max_speed=420.0f;
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
        materials_load(s->activity->assetManager,&mesh,&materials,"scene_materials.bin",AMALUR_SCENE_SHA256);
        character_load(s->activity->assetManager,&c.character);
        if(c.collision_ready&&c.character.ready){c.character.facing=c.walk_yaw;memcpy(c.character.feet,c.body.feet,sizeof(c.body.feet));}
        realm=opem_android_scripts_start(&mesh,s->activity->assetManager,&controller);
        oa_android_start(&interaction,realm,s->activity->assetManager,inventory_path);
        /* Test aid: adb shell setprop debug.opem.world town opens Gorhart without walking to the door. */
        {char prop[PROP_VALUE_MAX]={0};if(__system_property_get("debug.opem.world",prop)>0&&!strcmp(prop,"town")){world_request=1;c.spawn_hint=oa_doors[1];oa_menu_open(&menu,OA_SCREEN_GAME);}}
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
            if(s->active_window){ANativeWindow_acquire(s->active_window);graphics_open(&g,s->active_window,&mesh,&materials,&c.character,&c.npcs,&c.foe,c.sky_bytes,c.sky_size,world);}
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
            if(result==INPUT_IDENT)input_drain(s->attached_queue,&movement,&g,resumed&&focused,&interaction,inventory_path,&menu);}
        /* A wake may announce teardown or a focus loss. Recheck held state. */
        pthread_mutex_lock(&s->mutex);stop=s->stop;resumed=s->resumed;focused=s->focused;
        if(clear_epoch!=s->clear_input_epoch){exploration_input_clear(&movement);last_frame_ms=0;clear_epoch=s->clear_input_epoch;}
        {int draw=!stop&&resumed&&g.ready&&s->active_window==s->desired_window;
            pthread_mutex_unlock(&s->mutex);
            if(draw){
                /* Debug-only live feature comparison; does not change player/input state. */
                if(prof.on){static int64_t last_feature_poll;int64_t now=monotonic_ms();if(now-last_feature_poll>=500){int live=prop_int("debug.opem.live",255);last_feature_poll=now;if(live!=prof.live){LOGI("Renderer features changed old=%d new=%d",prof.live,live);prof.live=live;}}}
                oa_audio_set_active(active_audio,resumed&&focused);int64_t now=monotonic_ms();float dt=last_frame_ms?clampf((float)(now-last_frame_ms)*.001f,0,.05f):0;last_frame_ms=now;if(prof.slow>0)dt*=(float)prof.slow*.01f;
                if(movement.lighting_requested){room_lighting=!room_lighting;movement.lighting_requested=0;LOGI("Lighting comparison mode=%s",room_lighting?"room_source_points":"legacy_preview");}
                int playing;prof.start=now_ns();
                if(movement.menu_requested){movement.menu_requested=0;oa_menu_open(&menu,OA_SCREEN_PAUSE);}
                playing=menu.screen==OA_SCREEN_GAME;c.look_speed=menu.settings.look_speed;c.invert_look=menu.settings.invert_look;last_dt=dt;
                if(s->active_window!=rate_window||applied_rate!=menu.settings.rate){rate_window=s->active_window;applied_rate=menu.settings.rate;frame_rate_apply(rate_window,oa_menu_rate(&menu));}
                /* Equipped items drive combat, the visible weapon and potion healing. */
                c.combat.player_damage=oa_bag_damage(&menu.bag);c.combat.foe_damage=9.f*oa_armor_scale(oa_bag_armor(&menu.bag));
                if(menu.heal_request>0){c.combat.player_hp=clampf(c.combat.player_hp+menu.heal_request,0,c.combat.player_max);menu.heal_request=0;}
                if(c.character.part_count>=OA_WEAPON_MODELS){unsigned base=c.character.part_count-OA_WEAPON_MODELS,m;c.character.hidden=0;for(m=0;m<OA_WEAPON_MODELS;m++)if((int)m!=oa_bag_weapon_model(&menu.bag))c.character.hidden|=1u<<(base+m);/* The sword is drawn only for a fight; there is no sheathed model yet. */if(!c.character.combat_stance)for(m=0;m<OA_WEAPON_MODELS;m++)c.character.hidden|=1u<<(base+m);}
                if(c.foe_ready){int down=c.combat.foe==OA_FOE_DEAD;if(down&&!foe_down){static char loot[64];unsigned coin=12+(unsigned)(rand()%19);menu.bag.gold+=coin;{int roll=rand()%100,item=-1;/* Authored loot odds, so every item can be earned. */
                    if(roll<30)item=OA_ITEM_IRON+rand()%(OA_ITEM_ZODIAC_BOOTS-OA_ITEM_IRON+1);else if(roll<70)item=OA_ITEM_MINOR_POTION+(roll<45?1:0);
                    if(item>=0){oa_bag_add(&menu.bag,item,1);snprintf(loot,sizeof(loot),"Bandit dropped %u gold and %s",coin,oa_item_get(item)->name);}else snprintf(loot,sizeof(loot),"Bandit dropped %u gold",coin);}oa_menu_status(&menu,loot);LOGI("Loot %s",loot);}foe_down=down;}
                if(active_stream){opem_collision_world *next_world=oa_stream_collision_poll(active_stream,c.body.feet);if(next_world){int64_t swap_t=now_ns();opem_collision_destroy(c.world);c.world=next_world;LOGI("Stream collision swap feet=(%.0f %.0f) ms=%.2f",c.body.feet[0],c.body.feet[1],(now_ns()-swap_t)/1e6);}}
                /* Test aid: debug.opem.walk is a heading in degrees plus one. */
                /* Test aid: debug.opem.heading fixes the view in degrees plus one, so runs are comparable. */
                if(prof.heading&&playing){c.walk_yaw=(float)(prof.heading-1)*.01745329f;c.walk_pitch=-.05f;}
                if(prof.walk&&playing){movement.move_y=1.f;c.walk_yaw=(float)(prof.walk-1)*.01745329f;}
                /* Test aid: debug.opem.at "x y z" moves the player there once. */
                if(playing&&active_stream&&c.collision_ready){static int moved;if(!moved){char at_prop[PROP_VALUE_MAX]={0};float at[3];moved=1;if(__system_property_get("debug.opem.at",at_prop)>0&&sscanf(at_prop,"%f %f %f",&at[0],&at[1],&at[2])==3){char why[128]="";opem_collision_world *near_world=oa_stream_collision_now(active_stream,at,why,sizeof(why));if(near_world){opem_collision_destroy(c.world);c.world=near_world;if(opem_controller_spawn(c.world,&c.body_config,at,&c.body,why,sizeof(why))){memcpy(c.character.feet,c.body.feet,sizeof(c.body.feet));LOGI("Moved to (%.0f %.0f %.0f)",c.body.feet[0],c.body.feet[1],c.body.feet[2]);}else LOGE("Move rejected: %s",why);}}}}
                /* Test aid: debug.opem.tour holds the stick along a route computed from the zone's collision, so everything below runs as it does in play. */
                if(prof.tour&&playing&&active_stream&&c.collision_ready){static float *route,wait,here,stuck,last[2];static uint32_t count,next;float dx,dy,d;
                    if(!route){AAsset *as=AAssetManager_open(s->activity->assetManager,"actors/route.bin",AASSET_MODE_BUFFER);if(as){const uint8_t *rb=(const uint8_t*)AAsset_getBuffer(as);memcpy(&count,rb,4);route=(float*)malloc((size_t)count*12u);if(route)memcpy(route,rb+4,(size_t)count*12u);AAsset_close(as);LOGI("TOUR route waypoints=%u",count);}}
                    tour_frames++;if(!c.body.grounded)tour_air++;
                    if(route&&next<count){const float *w=route+next*3;dx=w[0]-c.body.feet[0];dy=w[1]-c.body.feet[1];d=sqrtf(dx*dx+dy*dy);here+=dt;
                        {float mx=c.body.feet[0]-last[0],my=c.body.feet[1]-last[1];if(here>.5f){stuck=mx*mx+my*my<30.f*30.f?stuck+here:0;here=0;last[0]=c.body.feet[0];last[1]=c.body.feet[1];}}
                        movement.move_y=0;movement.move_x=0;
                        if(d<(w[2]>0?150.f:220.f)){if(w[2]>0){if((wait+=dt)>6.f){wait=0;next++;tour_reached++;stuck=0;}}else{next++;stuck=0;}}
                        else{float t=remainderf(atan2f(dy,dx)-c.walk_yaw,6.283185307f),turn=dt*6.f;c.walk_yaw=remainderf(c.walk_yaw+(t>turn?turn:t<-turn?-turn:t),6.283185307f);movement.move_y=1.f;}
                        /* Past a blocked waypoint, on to the next. */
                        if(stuck>6.f){next++;stuck=0;tour_gave_up++;}
                        if(next>=count){next=0;}
                        c.walk_pitch=-.12f;}}
                if(playing)oa_npcs_update(&c.npcs,dt);
                if(prof.fight&&playing){static float tap;if((tap-=dt)<=0){tap=(float)prof.fight*.01f;movement.attack_requested=1;}}
                if(playing&&(!prof.on||prof.fight)&&(c.foe_ready||active_actors)&&c.collision_ready&&!interaction.window_open){oa_combat *f=&c.combat;char fight_error[256]="";static const float nobody[3]={1e7f,1e7f,0};
/* Test aid: debug.opem.pulse lets go of the stick every other period, in tenths of a second, so starts and stops can be seen. */if(prof_pulse&&playing&&(monotonic_ms()/(prof_pulse*100))%2){movement.move_y=0;movement.move_x=0;}
                    oa_combat_step(f,dt,movement.attack_requested&&focused,c.body.feet,c.character.facing,c.foe_ready?c.foe.feet:nobody);
                    /* Moving breaks out of a swing that has landed. */
                    if(oa_fight_is_swing(f->player_clip)&&!f->player_locked&&!f->queued&&movement.move_x*movement.move_x+movement.move_y*movement.move_y>.02f){f->player_clip=0;f->player_stage=0;f->player_free_at=0;f->stop_player=1;}
                    if(f->player_turn)c.character.facing=f->player_facing;
                    if(f->stop_player)oa_character_stop(&c.character);if(f->stop_foe)oa_character_stop(&c.foe);
                    if(f->play_player>=0)oa_character_play(&c.character,f->play_player,f->hold_player,f->play_player_rate);
                    if(f->play_foe>=0)oa_character_play(&c.foe,f->play_foe,f->hold_foe,1);
                    if(f->respawn_player){oa_character_stop(&c.character);c.spawn_hint=oa_doors[1];exploration_reset(&c);c.character.facing=c.walk_yaw;}
                    if(f->respawn_foe){const float place[3]={OA_FOE_SPAWN_X,OA_FOE_SPAWN_Y,OA_LIVE_START_Z+17.9f};oa_character_stop(&c.foe);if(opem_controller_spawn(c.world,&c.body_config,place,&c.foe_body,fight_error,sizeof(fight_error)))memcpy(c.foe.feet,c.foe_body.feet,sizeof(c.foe.feet));}
                    if(f->foe==OA_FOE_CHASE&&(f->foe_vx!=0||f->foe_vy!=0)){
                        /* Authored steering: when progress stalls against an obstacle, veer aside for a moment. */
                        float vx=f->foe_vx,vy=f->foe_vy,before[2]={c.foe_body.feet[0],c.foe_body.feet[1]};
                        if(c.foe_detour>0){float a=c.foe_detour_side*1.2f,ca=cosf(a),sa=sinf(a),rx=vx*ca-vy*sa;vy=vx*sa+vy*ca;vx=rx;c.foe_detour-=dt;}
                        if(opem_controller_step(c.world,&c.body_config,&c.foe_body,vx,vy,dt,fight_error,sizeof(fight_error)))memcpy(c.foe.feet,c.foe_body.feet,sizeof(c.foe.feet));
                        {float mx=c.foe_body.feet[0]-before[0],my=c.foe_body.feet[1]-before[1],wanted=sqrtf(vx*vx+vy*vy)*dt;
                         c.foe_stuck=(wanted>.01f&&mx*mx+my*my<wanted*wanted*.09f)?c.foe_stuck+dt:0;
                         if(c.foe_stuck>.3f&&c.foe_detour<=0){c.foe_detour=1.1f;c.foe_detour_side=c.foe_detour_side>0?-1.f:1.f;c.foe_stuck=0;}}}
                    else if(c.foe_ready&&f->foe!=OA_FOE_DEAD&&opem_controller_step(c.world,&c.body_config,&c.foe_body,0,0,dt,fight_error,sizeof(fight_error)))memcpy(c.foe.feet,c.foe_body.feet,sizeof(c.foe.feet));
                    c.foe.facing=f->foe_facing;c.move_scale=f->player_locked?0.f:1.f;
                    if(c.foe_ready&&now-c.foe_log_ms>1500){c.foe_log_ms=now;LOGI("Fight foe=%d foe_at=(%.0f %.0f %.0f) me=(%.0f %.0f %.0f) hp=%.0f/%.0f detour=%.2f err=%s",(int)f->foe,c.foe.feet[0],c.foe.feet[1],c.foe.feet[2],c.body.feet[0],c.body.feet[1],c.body.feet[2],f->player_hp,f->foe_hp,c.foe_detour,fight_error);}
                    {float vx=f->foe_vx,vy=f->foe_vy;float speed=sqrtf(vx*vx+vy*vy);oa_character_animate(&c.foe,speed>1?1.f:0.f,speed,dt);oa_character_pose(&c.foe);}}
                if(playing&&active_actors&&c.collision_ready&&!interaction.window_open){oa_combat *f=&c.combat;oa_actors_frame af;
                     oa_actors_update(active_actors,c.world,c.body.feet,c.character.facing,!f->player_dead,f->swing_landed?f->player_damage:0.f,dt,&af);
                     if(af.has_turn&&oa_fight_is_swing(f->play_player))c.character.facing=af.turn_yaw;
                     /* Test runs measure the fight without ending it. */
                     if(af.damage>0&&!prof.on){f->play_player=-1;oa_combat_hurt_player(f,af.damage*f->foe_damage/9.f);if(f->play_player>=0)oa_character_play(&c.character,f->play_player,f->hold_player,f->play_player_rate);c.move_scale=f->player_dead||f->player_clip?0.f:1.f;}
                     if(af.hits&&active_audio)oa_audio_play(active_audio,snd_hit,NULL,.7f,1.f);if(af.kills){static char loot[64];unsigned coin=4+(unsigned)(rand()%12);menu.bag.gold+=coin;snprintf(loot,sizeof(loot),"%s slain, %u gold",af.killed,coin);oa_menu_status(&menu,loot);}}
                 {static float stance_time;float focus_hp;const char *focus_name;const oa_combat *f=&c.combat;float fx=c.foe.feet[0]-c.body.feet[0],fy=c.foe.feet[1]-c.body.feet[1];
                  if(movement.attack_requested||f->player_clip||f->player_dead||(c.foe_ready&&(f->foe==OA_FOE_CHASE||f->foe==OA_FOE_ATTACK||f->foe==OA_FOE_HIT)&&fx*fx+fy*fy<2200.f*2200.f)||oa_actors_focus(active_actors,c.body.feet,&focus_hp,&focus_name))stance_time=4.f;else if(stance_time>0)stance_time-=dt;c.character.combat_stance=stance_time>0;}
                 if(playing&&active_audio&&c.collision_ready){const oa_combat *f=&c.combat;float mv=movement.move_x*movement.move_x+movement.move_y*movement.move_y;static float phase;static int was_dead;
                    oa_audio_listener(active_audio,c.body.feet,c.walk_yaw);
                    if(mv>.01f&&c.body.grounded){int run=mv>.5f;const oa_char_clip *k=c.character.clips+(run?OA_CLIP_RUN:OA_CLIP_WALK);float seconds=(float)(k->frames-1)/k->fps,was=phase;float rate=(run?420.f:420.f*sqrtf(mv))/(c.character.clip_speed[run?OA_CLIP_RUN:OA_CLIP_WALK]>1.f?c.character.clip_speed[run?OA_CLIP_RUN:OA_CLIP_WALK]:420.f);phase=fmodf(phase+dt*rate/seconds*2.f,1.f);if(phase<was)oa_audio_play(active_audio,snd_foot,NULL,.35f,1.f);}
                    if(oa_fight_is_swing(f->play_player))oa_audio_play(active_audio,snd_use,NULL,.6f,1.f);
                    if(f->swing_landed&&(f->foe_struck))oa_audio_play(active_audio,snd_hit,NULL,.7f,1.f);
                    if(f->player_dead&&!was_dead)oa_audio_play(active_audio,snd_die,NULL,.8f,1.f);was_dead=f->player_dead;}
movement.attack_requested=0;
                 if(prof.tour&&active_stream&&playing)movement.look_dx=movement.look_dy=0;
                if(focused&&!interaction.window_open&&playing)exploration_update(&c,&movement,dt);else{exploration_input_clear(&movement);if(playing)last_frame_ms=0;}
                if(!interaction.window_open&&playing){
                    interaction.selected.generation=0;
                    if(world==0&&c.walking&&c.collision_ready&&interaction.ready){
                        float eye[3]={c.body.feet[0],c.body.feet[1],c.body.feet[2]+c.body_config.height*.9f};
                        float direction[3]={cosf(c.walk_pitch)*cosf(c.walk_yaw),cosf(c.walk_pitch)*sinf(c.walk_yaw),sinf(c.walk_pitch)},hit[3],distance,occlusion;
                        if(oa_mesh_pick(mesh.vertices,mesh.vertex_count,OA_WORKBENCH_FIRST_VERTEX,OA_WORKBENCH_VERTEX_COUNT,eye,direction,300,hit,&distance)&&opem_collision_ray(c.world,eye,direction,300,&occlusion)&&occlusion+.5f>=distance&&oa_object_target(&interaction.registry,interaction.workbench,hit)&&oa_workbench_in_reach(&interaction.registry,interaction.workbench,c.body.feet,c.walk_yaw))interaction.selected=interaction.workbench;
                    }
                    door_prompt=NULL;
                    if(c.walking&&c.collision_ready&&world_request<0){const float *door=oa_doors[world];float dx=c.body.feet[0]-door[0],dy=c.body.feet[1]-door[1],dz=c.body.feet[2]-door[2];
                        if(OA_LIVE_HAS_SHOP&&dx*dx+dy*dy<260.f*260.f&&fabsf(dz)<220.f&&!interaction.selected.generation){door_prompt=oa_door_prompts[world];
                            if(movement.interact_requested){movement.interact_requested=0;world_request=!world;c.spawn_hint=oa_doors[world_request];}}}
                    if(movement.interact_requested){char error[256];movement.interact_requested=0;if(interaction.selected.generation){if(oa_lua_interact(realm,&interaction,error,sizeof(error)))LOGE("Workbench original Lua callback failed: %s",error);else{LOGI("Workbench original Lua on_interact opened authored alchemy window source=524875");exploration_input_clear(&movement);}}}
                }
                if(world_request>=0){int next=world_request;world_request=-1;door_prompt=NULL;
                    {int64_t load_t=now_ns();pthread_mutex_lock(&s->mutex);graphics_close(&g);world_load(s->activity->assetManager,next,&mesh,&materials,&c);world=next;LOGI("PROFILE world_load_ms=%.0f",(now_ns()-load_t)/1e6);}
                    if(s->active_window)graphics_open(&g,s->active_window,&mesh,&materials,&c.character,&c.npcs,&c.foe,c.sky_bytes,c.sky_size,world);pthread_mutex_unlock(&s->mutex);
                    if(c.collision_ready){c.character.facing=c.walk_yaw;memcpy(c.character.feet,c.body.feet,sizeof(c.body.feet));oa_character_pose(&c.character);}
                    if(pending_load&&c.collision_ready){pending_load=0;c.walk_yaw=loaded.yaw;c.walk_pitch=loaded.pitch;c.character.facing=loaded.yaw;c.combat.player_hp=clampf(loaded.health,1,c.combat.player_max);oa_character_pose(&c.character);}
                    exploration_input_clear(&movement);last_frame_ms=0;lighting_started_ms=0;
                    if(!g.ready)continue;}
                if(observed_lighting_mode!=room_lighting||!lighting_started_ms){observed_lighting_mode=room_lighting;lighting_started_ms=now;lighting_frames=0;}
                if(++lighting_frames==120){LOGI("Lighting frame observation mode=%s frames=120 elapsed_ms=%lld mean_interval_ms=%.3f scope=active_worker_frame_intervals",room_lighting?"room":"preview",(long long)(now-lighting_started_ms),(double)(now-lighting_started_ms)/119.0);}
                if(!graphics_draw(&g,&mesh,&materials,&c,&movement,&interaction,room_lighting,door_prompt,&menu,world,last_dt)){pthread_mutex_lock(&s->mutex);graphics_close(&g);pthread_mutex_unlock(&s->mutex);}
                switch(menu.action){
                    case OA_ACTION_NEW_GAME:c.spawn_hint=NULL;pending_load=0;oa_bag_new(&menu.bag);oa_menu_open(&menu,OA_SCREEN_GAME);
                        if(world!=0)world_request=0;else{exploration_reset(&c);oa_combat_reset(&c.combat);oa_character_stop(&c.character);c.character.facing=c.walk_yaw;memcpy(c.character.feet,c.body.feet,sizeof(c.body.feet));oa_character_pose(&c.character);}
                        LOGI("Menu new game");break;
                    case OA_ACTION_LOAD:if(oa_save_read(&loaded,menu.save_path)){menu.bag=loaded.bag;c.spawn_hint=loaded.feet;oa_menu_open(&menu,OA_SCREEN_GAME);pending_load=1;
                            if(world!=loaded.world)world_request=loaded.world;
                            else{exploration_reset(&c);memcpy(c.character.feet,c.body.feet,sizeof(c.body.feet));if(c.collision_ready){pending_load=0;c.walk_yaw=loaded.yaw;c.walk_pitch=loaded.pitch;c.character.facing=loaded.yaw;c.combat.player_hp=clampf(loaded.health,1,c.combat.player_max);oa_character_pose(&c.character);}}
                            LOGI("Menu loaded save world=%d feet=(%.0f %.0f %.0f) ready=%d",loaded.world,loaded.feet[0],loaded.feet[1],loaded.feet[2],c.collision_ready);}
                        else oa_menu_status(&menu,"No saved game could be read");break;
                    case OA_ACTION_SAVE:{oa_save save;memset(&save,0,sizeof(save));save.world=world;memcpy(save.feet,c.body.feet,sizeof(save.feet));save.yaw=c.walk_yaw;save.pitch=c.walk_pitch;save.health=c.combat.player_hp;save.bag=menu.bag;
                        if(c.collision_ready&&oa_save_write(&save,menu.save_path)){menu.has_save=1;oa_menu_status(&menu,"Game saved");LOGI("Menu saved world=%d",world);}else oa_menu_status(&menu,"Could not save");break;}
                    case OA_ACTION_EXIT:LOGI("Menu exit");ANativeActivity_finish(s->activity);break;
                    case OA_ACTION_TOGGLE_LIGHTING:room_lighting=!room_lighting;break;
                    case OA_ACTION_APPLY_RATE:case OA_ACTION_NONE:default:break;}
                menu.action=OA_ACTION_NONE;
            }else last_frame_ms=0;
        }
    }
    oa_audio_close(active_audio);active_audio=NULL;oa_actors_close(active_actors);active_actors=NULL;oa_stream_close(active_stream);active_stream=NULL;
    opem_android_scripts_stop(realm);
    free(ui_bytes);ui_bytes=NULL;ui_size=0;
    oa_android_close(&interaction);
    input_host_close(&inputs,s->activity->vm);
    scene_materials_v09_free(&materials);
    oa_npcs_free(&c.npcs);
    free(c.sky_bytes);
    if(c.foe.bytes)oa_character_free(&c.foe);
    oa_character_free(&c.character);
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
