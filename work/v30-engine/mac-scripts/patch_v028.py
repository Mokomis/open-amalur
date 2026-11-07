"""Version 0.27.0: live-play renderer. Materials, all point lights, fog, bloom, ambient occlusion, foliage, crowd and effects load."""
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
host = root / "work/v19-host"
pending = []
def stage(path, pairs):
    f = host / path
    t = f.read_bytes().decode("utf-8")
    for old, new in pairs:
        if t.count(old) != 1 and t.count(old.replace("\n", "\r\n")) == 1:
            old = old.replace("\n", "\r\n")
        if t.count(old) != 1:
            raise SystemExit("%s: expected one match for %r, found %d" % (path, old[:90], t.count(old)))
        t = t.replace(old, new)
    pending.append((f, t))
stage("android_scene.cmake", [("oa_items.c oa_stream.c ", "oa_items.c oa_stream.c oa_post.c ")])
stage("CMakeLists.txt", [("VERSION 0.26.0", "VERSION 0.27.0")])
stage("AndroidManifest.xml", [('android:versionCode="28" android:versionName="0.26.0"', 'android:versionCode="29" android:versionName="0.27.0"')])
stage("package_android.py", [("opem-amalur-scene-v0.26-arm64.apk", "opem-amalur-scene-v0.27-arm64.apk"), ("str(root/'work/v22-stress/zone-pack')", "str(root/'work/v22-stress/live-pack')")])
stage("oa_menu.c", [('"v0.26.0"', '"v0.27.0"')])
stage("room_lighting.h", [("const float *opem_town_sun(void);", "const float *opem_town_sun(void);\nconst float *opem_town_sun_rgb(void);\nconst float *opem_town_shadow_rgba(void);")])
stage("room_lighting.c", [("const float *opem_town_sun(void){return opem_town_sun_direction;}", "const float *opem_town_sun(void){return opem_town_sun_direction;}\nconst float *opem_town_sun_rgb(void){return opem_town_sun_color;}\nconst float *opem_town_shadow_rgba(void){return opem_town_shadow_color;}"),
 (' s->outdoor=outdoor;\n', ' s->outdoor=outdoor;\n /* Outdoors the color table is applied once, in the final post pass. */\n glUseProgram(program);glUniform1i(glGetUniformLocation(program,"room_no_lut"),outdoor);\n')])
stage("room_lighting_shader.h", [('uniform int room_mode;uniform int room_light_count;', 'uniform int room_mode;uniform int room_no_lut;uniform int room_light_count;'),
 ('if(room_mode!=0)lit=texture(room_lut,', 'if(room_mode!=0&&room_no_lut==0)lit=texture(room_lut,')])
stage("oa_sky.c", [('uniform float time;out vec4 color;"', 'uniform float time;uniform int raw;out vec4 color;"'),
 ('"color=vec4(texture(lut,clamp(c,0.0,1.0)*.9375+.03125).rgb,1.0);}";', '"color=raw!=0?vec4(c,1.0):vec4(texture(lut,clamp(c,0.0,1.0)*.9375+.03125).rgb,1.0);}";'),
 ('glUniform1f(s->time,seconds);', 'glUniform1f(s->time,seconds);glUniform1i(glGetUniformLocation(s->program,"raw"),lut==0);')])
stage("android_scene.c", [
 ('#include "oa_stream.h"\n', '#include "oa_stream.h"\n#include "oa_post.h"\n#include "town_live.inc"\n'),
 ("    GLuint shadow_fbo,shadow_tex;\n} graphics;", "    GLuint shadow_fbo,shadow_tex,world_program;\n    oa_post post;\n} graphics;"),
 ("oa_stream_gpu_close(active_stream);if(g->shadow_tex)", "oa_stream_gpu_close(active_stream);oa_post_close(&g->post);if(g->world_program)glDeleteProgram(g->world_program);if(g->shadow_tex)"),
 ("static struct{int on,skip,scale,crowd,shadow,walk,tour,far_m,tour_m;", "static struct{int on,skip,scale,crowd,shadow,walk,tour,far_m,tour_m,live,fx;"),
 ('stream_far=(float)prof.far_m*100.0f;}', 'stream_far=(float)prof.far_m*100.0f;prof.live=prop_int("debug.opem.live",15);prof.fx=prop_int("debug.opem.fx",0);}'),
 ("    if(!exploration_overlay_open(&g->overlay)){", """    if(active_stream){EGLint sw=0,sh=0;eglQuerySurface(g->display,g->surface,EGL_WIDTH,&sw);eglQuerySurface(g->display,g->surface,EGL_HEIGHT,&sh);g->world_program=oa_post_program(oa_world_vertex,oa_world_fragment);if(!g->world_program)LOGE("World shader unavailable");oa_post_open(&g->post,sw,sh);}
    if(!exploration_overlay_open(&g->overlay)){"""),
 ("if(g->sky.ready&&!(prof.skip&1))oa_sky_draw(&g->sky,matrix,eye,c->radius*8.0f,(float)(monotonic_ms()%3600000)*.001f,g->room_lights.lut);", "{int live_post=active_stream&&g->post.ready&&g->world_program;if(live_post){oa_post_begin(&g->post);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);}\n        if(g->sky.ready&&!(prof.skip&1))oa_sky_draw(&g->sky,matrix,eye,fminf(c->radius*8.0f,stream_far*1.4f),(float)(monotonic_ms()%3600000)*.001f,live_post?0:g->room_lights.lut);}"),
 ("        if(prof.skip&2){}else if(active_stream)oa_stream_draw(active_stream,matrix,g->has_texture_location,g->sampler_location,eye,0);else if", """        if(prof.skip&2){}else if(active_stream&&g->world_program)world_draw(g,matrix,eye,shadow_on,shadow_matrix);else if"""),
 ("oa_stream_draw(active_stream,shadow_matrix,g->has_texture_location,g->sampler_location,c->body.feet,half*1.5f);", "glUniform1i(g->sampler_location,0);oa_stream_draw(active_stream,shadow_matrix,g->has_texture_location,-1,c->body.feet,half*1.5f);"),
 ("if(!(prof.skip&4)){unsigned p;int n;for(n=0;n<prof.crowd;n++)for(p=0;p<c->npcs.count;p++)oa_character_gpu_draw(&g->people[p],c->npcs.people+p,matrix,room_lighting,.5f);}}", """if(!(prof.skip&4)){unsigned p;int n;for(n=0;n<prof.crowd;n++)for(p=0;p<c->npcs.count;p++){oa_character *person=(oa_character*)(c->npcs.people+p);float kept[3];
            /* Crowd load: each extra person is posed on the CPU and placed around the player, as a live crowd would be. */
            if(n){float a=(float)(n*12+p)*2.399963f,r=350.f+(float)n*90.f;memcpy(kept,person->feet,sizeof(kept));person->feet[0]=c->body.feet[0]+cosf(a)*r;person->feet[1]=c->body.feet[1]+sinf(a)*r;person->feet[2]=c->body.feet[2];oa_character_pose(person);}
            oa_character_gpu_draw(&g->people[p],person,matrix,room_lighting,.5f);
            if(n){memcpy(person->feet,kept,sizeof(kept));oa_character_pose(person);}}}
        if(active_stream&&g->post.ready&&g->world_program){if(prof.fx)oa_post_fx(&g->post,matrix,eye,c->body.feet,prof.fx,(float)(monotonic_ms()%3600000)*.001f);
            oa_post_end(&g->post,g->room_lights.lut,oa_live_bloom,oa_live_bloom_cut,2.0f,stream_far*1.6f,(prof.live&2)!=0,(prof.live&1)!=0,width,height);}}"""),
 ("static int graphics_draw(graphics *g,", """/* Sets the outdoor material shader up, chooses the nearest real lights, and draws the streamed world. */
static void world_draw(graphics *g,const float mvp[16],const float eye[3],int shadow_on,const float shadow_matrix[16]){
    GLuint w=g->world_program;float lp[12*4],lc[12*4],best[12];int n=0,i,k;const float *sun=opem_town_sun(),*sc=opem_town_sun_rgb(),*sh=opem_town_shadow_rgba();
    glUseProgram(w);glUniformMatrix4fv(glGetUniformLocation(w,"mvp"),1,GL_FALSE,mvp);glUniform3fv(glGetUniformLocation(w,"eye"),1,eye);glUniform3fv(glGetUniformLocation(w,"sun_color"),1,sc);glUniform3fv(glGetUniformLocation(w,"sun_dir"),1,sun);glUniform3fv(glGetUniformLocation(w,"shadow_color"),1,sh);glUniform3fv(glGetUniformLocation(w,"fog_color"),1,oa_live_fog_color);glUniform2f(glGetUniformLocation(w,"fog"),oa_live_fog_start,oa_live_fog_density);glUniform1i(glGetUniformLocation(w,"features"),prof.live);glUniform1i(glGetUniformLocation(w,"shadow_on"),shadow_on);
    {static const char *names[6]={"t0","t1","t2","t3","t4","t5"};for(i=0;i<6;i++)glUniform1i(glGetUniformLocation(w,names[i]),i);}
    glUniform1i(glGetUniformLocation(w,"cube"),8);glUniform1i(glGetUniformLocation(w,"shadow_map"),9);
    glActiveTexture(GL_TEXTURE8);glBindTexture(GL_TEXTURE_CUBE_MAP,g->room_lights.cube);
    if(shadow_on){glActiveTexture(GL_TEXTURE9);glBindTexture(GL_TEXTURE_2D,g->shadow_tex);glUniformMatrix4fv(glGetUniformLocation(w,"shadow_matrix"),1,GL_FALSE,shadow_matrix);}
    for(i=0;i<OA_LIVE_LIGHTS;i++){const float *l=oa_live_lights[i];float dx=l[0]-eye[0],dy=l[1]-eye[1],dz=l[2]-eye[2],d=dx*dx+dy*dy+dz*dz,reach=l[7]+6000.f;if(d>reach*reach)continue;
        for(k=n<12?n:12;k>0&&best[k-1]>d;k--){if(k<12){best[k]=best[k-1];memcpy(lp+k*4,lp+(k-1)*4,16);memcpy(lc+k*4,lc+(k-1)*4,16);}}
        if(k<12){best[k]=d;memcpy(lp+k*4,l,16);memcpy(lc+k*4,l+4,16);if(n<12)n++;}}
    glUniform1i(glGetUniformLocation(w,"light_count"),n);if(n){glUniform4fv(glGetUniformLocation(w,"lp"),n,lp);glUniform4fv(glGetUniformLocation(w,"lc"),n,lc);}
    oa_stream_draw(active_stream,mvp,-1,glGetUniformLocation(w,"terrain"),eye,0);
    glActiveTexture(GL_TEXTURE0);
}
static int graphics_draw(graphics *g,"""),
 ('{oa_stream_stats st;oa_stream_get_stats(active_stream,&st);LOGI("STREAM cells=', '{oa_stream_stats st;oa_stream_get_stats(active_stream,&st);LOGI("STREAM cells='),
])
for f, t in pending:
    f.write_bytes(t.encode("utf-8"))
print("patched", len(pending))
