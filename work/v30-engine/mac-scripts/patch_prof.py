"""Frame profiler and stress-test switches. Off unless debug.opem.profile is set."""
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
host = root / "work/v19-host"
def edit(path, pairs):
    f = Path(path) if Path(path).is_absolute() else host / path
    t = f.read_bytes().decode("utf-8")
    for old, new in pairs:
        if t.count(old) != 1 and t.count(old.replace("\n", "\r\n")) == 1:
            old = old.replace("\n", "\r\n")
        if t.count(old) != 1:
            raise SystemExit("%s: expected one match for %r, found %d" % (path, old[:90], t.count(old)))
        t = t.replace(old, new)
    f.write_bytes(t.encode("utf-8"))
# Builder, CMake and manifest edits were applied by the first, stopped run.
edit("android_scene.c", [
 ("static int graphics_draw(graphics *g,", """/* Stress-test instrumentation, inert unless adb sets debug.opem.profile.
 * profile=1 logs, profile=2 also disables vsync; skip bits: 1 sky, 2 scene, 4 people, 8 UI; scale is a render scale percent. */
static struct{int on,skip,scale;int64_t start,last,sim,submit,swap,worst;unsigned frames;GLuint query[8];unsigned qi;uint64_t gpu,gpu_max;unsigned gpu_n;int timer;}prof;
static int64_t now_ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (int64_t)t.tv_sec*1000000000+t.tv_nsec;}
static int prop_int(const char *name,int fallback){char v[PROP_VALUE_MAX]={0};return __system_property_get(name,v)>0?atoi(v):fallback;}
static void prof_read(void){prof.on=prop_int("debug.opem.profile",0);prof.skip=prop_int("debug.opem.skip",0);prof.scale=prop_int("debug.opem.scale",100);}
static void prof_gl_start(void){const char *x=(const char*)glGetString(GL_EXTENSIONS);prof.timer=prof.on&&x&&strstr(x,"GL_EXT_disjoint_timer_query");if(prof.timer){glGenQueries(8,prof.query);prof.qi=0;}LOGI("Profile on=%d skip=%d scale=%d gpu_timer=%d renderer=%s",prof.on,prof.skip,prof.scale,prof.timer,(const char*)glGetString(GL_RENDERER));}
static int graphics_draw(graphics *g,"""),
 ("    eglSwapInterval(g->display,1);", "    eglSwapInterval(g->display,prof.on==2?0:1);prof_gl_start();"),
 ("ANativeWindow_setBuffersGeometry(window,0,0,format)!=0", "ANativeWindow_setBuffersGeometry(window,prof.scale!=100?ANativeWindow_getWidth(window)*prof.scale/100:0,prof.scale!=100?ANativeWindow_getHeight(window)*prof.scale/100:0,format)!=0"),
 ("    float hud[3];EGLint width,height;", "    float hud[3];EGLint width,height;int64_t prof_t0=now_ns();\n    if(prof.timer){glBeginQuery(0x88BF,prof.query[prof.qi]);}"),
 ("if(g->sky.ready)oa_sky_draw(", "if(g->sky.ready&&!(prof.skip&1))oa_sky_draw("),
 ("        if(g->materials.ready&&!scene_material_renderer_v09_draw(", "        if(prof.skip&2){}else if(g->materials.ready&&!scene_material_renderer_v09_draw("),
 ("        if(!g->materials.ready){glUniform1i(g->has_texture_location,0);", "        if(!g->materials.ready&&!(prof.skip&2)){glUniform1i(g->has_texture_location,0);"),
 ("        if(c->foe_ready)oa_character_gpu_draw(", "        if(c->foe_ready&&!(prof.skip&4))oa_character_gpu_draw("),
 ("        {unsigned p;for(p=0;p<c->npcs.count;p++)oa_character_gpu_draw(", "        if(!(prof.skip&4)){unsigned p;for(p=0;p<c->npcs.count;p++)oa_character_gpu_draw("),
 ("oa_ui_begin(&g->ui);if(g->ui.ready)oa_menu_frame(", "oa_ui_begin(&g->ui);if(g->ui.ready&&!(prof.skip&8))oa_menu_frame("),
 ("""    if(!eglSwapBuffers(g->display,g->surface)){LOGE("EGL swap failed:0x%x",eglGetError());return 0;}
    return 1;""", """    {int64_t t1,t2;
     if(prof.timer){GLuint ready=0,ns=0,q;GLint disjoint=0;glEndQuery(0x88BF);prof.qi=(prof.qi+1)%8;q=prof.query[prof.qi];glGetQueryObjectuiv(q,GL_QUERY_RESULT_AVAILABLE,&ready);glGetIntegerv(0x8FBB,&disjoint);if(ready&&!disjoint){glGetQueryObjectuiv(q,GL_QUERY_RESULT,&ns);if(ns){prof.gpu+=ns;prof.gpu_n++;if(ns>prof.gpu_max)prof.gpu_max=ns;}}}
     t1=now_ns();
     if(!eglSwapBuffers(g->display,g->surface)){LOGE("EGL swap failed:0x%x",eglGetError());return 0;}
     t2=now_ns();
     if(prof.on){int64_t gap=prof.last?t2-prof.last:0;prof.last=t2;prof.sim+=prof_t0-prof.start;prof.submit+=t1-prof_t0;prof.swap+=t2-t1;if(gap>prof.worst)prof.worst=gap;
      if(++prof.frames==240){LOGI("PROFILE interval_ms=%.2f worst_ms=%.2f sim_ms=%.2f submit_ms=%.2f swap_ms=%.2f gpu_ms=%.2f gpu_max_ms=%.2f gpu_samples=%u size=%dx%d vertices=%u",(double)(t2-prof.start+prof.sim*0)/1e6*0+(prof.sim+prof.submit+prof.swap)/240.0/1e6,(double)prof.worst/1e6,prof.sim/240.0/1e6,prof.submit/240.0/1e6,prof.swap/240.0/1e6,prof.gpu_n?(double)prof.gpu/prof.gpu_n/1e6:-1.0,(double)prof.gpu_max/1e6,prof.gpu_n,width,height,mesh->vertex_count);prof.frames=0;prof.sim=prof.submit=prof.swap=prof.worst=0;prof.gpu=prof.gpu_max=0;prof.gpu_n=0;}}}
    return 1;"""),
 ("    snprintf(inventory_path,sizeof(inventory_path),\"%s/%s\",s->activity->internalDataPath,\"opem-inventory-v1.bin\");", "    prof_read();\n    snprintf(inventory_path,sizeof(inventory_path),\"%s/%s\",s->activity->internalDataPath,\"opem-inventory-v1.bin\");"),
 ("                int playing;\n", "                int playing;prof.start=now_ns();\n"),
 ("if(playing&&c.foe_ready&&c.collision_ready&&!interaction.window_open){", "if(playing&&!prof.on&&c.foe_ready&&c.collision_ready&&!interaction.window_open){"),
 ('LOGI("World switched to %s ready=%d",world?"gorhart":"shop",c->collision_ready);', 'LOGI("World switched to %s ready=%d vertices=%u draws=%u textures=%u",world?"gorhart":"shop",c->collision_ready,mesh->vertex_count,materials->draw_count,materials->texture_count);'),
 ("                    pthread_mutex_lock(&s->mutex);graphics_close(&g);world_load(s->activity->assetManager,next,&mesh,&materials,&c);world=next;", "                    {int64_t load_t=now_ns();pthread_mutex_lock(&s->mutex);graphics_close(&g);world_load(s->activity->assetManager,next,&mesh,&materials,&c);world=next;LOGI(\"PROFILE world_load_ms=%.0f\",(now_ns()-load_t)/1e6);}"),
])
print("patched")
