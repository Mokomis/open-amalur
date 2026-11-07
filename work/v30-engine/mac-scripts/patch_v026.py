"""Version 0.26.0: world streaming, LOD, background collision, optional sun shadow map."""
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
    return f, t
pending = []
def stage(path, pairs):
    pending.append(edit(path, pairs))
stage("android_scene.cmake", [("oa_ui.c oa_menu.c oa_items.c ", "oa_ui.c oa_menu.c oa_items.c oa_stream.c ")])
stage("CMakeLists.txt", [("VERSION 0.25.1", "VERSION 0.26.0")])
stage("AndroidManifest.xml", [('android:versionCode="27" android:versionName="0.25.1"', 'android:versionCode="28" android:versionName="0.26.0"')])
stage("package_android.py", [("opem-amalur-scene-v0.25-arm64.apk", "opem-amalur-scene-v0.26-arm64.apk"),
 ("files['assets/oa_ui.bin']=root/'work/v21-ui/oa_ui.bin'", "files['assets/oa_ui.bin']=root/'work/v21-ui/oa_ui.bin'\nimport os as _os\nfor _p in Path(_os.environ.get('OA_WORLD_DIR',str(root/'work/v22-stress/pack'))).glob('*.bin'):files['assets/world/'+_p.name]=_p")])
stage("room_lighting.h", [("const char *opem_room_lighting_identity(void);", "const char *opem_room_lighting_identity(void);\nconst float *opem_town_sun(void);")])
stage("room_lighting.c", [("const char *opem_room_lighting_identity(void){return identity;}", "const char *opem_room_lighting_identity(void){return identity;}\nconst float *opem_town_sun(void){return opem_town_sun_direction;}")])
stage("room_lighting_shader.h", [
 ("Not implemented: specular, SSAO, shadow maps, fog, bloom.", "The sun shadow map is an authored host choice, not the game's filtering. Not implemented: specular, SSAO, fog, bloom."),
 ('precision highp sampler3D;\\n"', 'precision highp sampler3D;precision highp sampler2DShadow;\\n"'),
 ('uniform vec4 room_color_outer[36];"', 'uniform vec4 room_color_outer[36];uniform sampler2DShadow room_shadow_map;uniform mat4 room_shadow_matrix;uniform int room_shadow_on;"'),
 ('float sunTerm=clamp(dot(N,room_sun_direction),0.0,1.0);', 'float sunTerm=clamp(dot(N,room_sun_direction),0.0,1.0);if(room_shadow_on!=0&&sunTerm>0.0){vec4 q=room_shadow_matrix*vec4(world_position,1.0);vec3 s=q.xyz*0.5+0.5;if(s.x>0.0&&s.x<1.0&&s.y>0.0&&s.y<1.0&&s.z<1.0){float t=0.00049;float v=texture(room_shadow_map,vec3(s.xy+vec2(-t,-t),s.z))+texture(room_shadow_map,vec3(s.xy+vec2(t,-t),s.z))+texture(room_shadow_map,vec3(s.xy+vec2(-t,t),s.z))+texture(room_shadow_map,vec3(s.xy+vec2(t,t),s.z));sunTerm*=v*0.25;}}'),
])
stage("android_scene.c", [
 ('#include "oa_items.h"\n', '#include "oa_items.h"\n#include "oa_stream.h"\n'),
 ("    oa_ui ui;\n} graphics;", "    oa_ui ui;\n    GLuint shadow_fbo,shadow_tex;\n} graphics;"),
 ("/* Worker-only UI asset, kept for surface recreation. */", "/* Worker-only streamed world while outdoors. */\nstatic oa_stream *active_stream;\n/* Worker-only UI asset, kept for surface recreation. */"),
 ("        exploration_overlay_close(&g->overlay);oa_ui_close(&g->ui);", "        exploration_overlay_close(&g->overlay);oa_ui_close(&g->ui);oa_stream_gpu_close(active_stream);if(g->shadow_tex)glDeleteTextures(1,&g->shadow_tex);if(g->shadow_fbo)glDeleteFramebuffers(1,&g->shadow_fbo);"),
 ("static struct{int on,skip,scale,crowd;", "static struct{int on,skip,scale,crowd,shadow,walk,tour;"),
 ('prof.crowd=prop_int("debug.opem.crowd",1);}', 'prof.crowd=prop_int("debug.opem.crowd",1);prof.shadow=prop_int("debug.opem.shadow",0);prof.walk=prop_int("debug.opem.walk",0);prof.tour=prop_int("debug.opem.tour",0);}'),
 ("    if(mesh->vertices){\n        g->program=program_create();", "    if(mesh->vertices||active_stream){\n        g->program=program_create();"),
 ("float near_plane=fmaxf(c->radius*0.001f,1e-7f),far_plane=c->distance+c->radius*40.0f;", "float near_plane=fmaxf(c->radius*0.001f,1e-7f),far_plane=active_stream&&c->walking?120000.0f:c->distance+c->radius*40.0f;"),
 ("    if(mesh->vertices&&menu->screen!=OA_SCREEN_TITLE", "    if((mesh->vertices||active_stream)&&menu->screen!=OA_SCREEN_TITLE"),
 ("{float matrix[16],eye[3];camera_matrix(c,(float)width/(float)height,matrix,eye);\n", """{float matrix[16],eye[3],shadow_matrix[16];int shadow_on=0;camera_matrix(c,(float)width/(float)height,matrix,eye);
        if(active_stream)oa_stream_update(active_stream,eye);
        /* Sun shadow map around the player, a stress-test switch until its cost is settled. */
        if(active_stream&&prof.shadow&&c->walking&&g->program){
            enum{SIZE=2048};const float *sun=opem_town_sun();float half=(float)prof.shadow*100.0f,pos[3],side[3],up[3],zup[3]={0,0,1},fwd[3],view[16]={0},proj[16]={0},snap;int a;
            if(!g->shadow_fbo){glGenTextures(1,&g->shadow_tex);glBindTexture(GL_TEXTURE_2D,g->shadow_tex);glTexStorage2D(GL_TEXTURE_2D,1,GL_DEPTH_COMPONENT24,SIZE,SIZE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_COMPARE_MODE,GL_COMPARE_REF_TO_TEXTURE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_COMPARE_FUNC,GL_LEQUAL);glGenFramebuffers(1,&g->shadow_fbo);glBindFramebuffer(GL_FRAMEBUFFER,g->shadow_fbo);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_DEPTH_ATTACHMENT,GL_TEXTURE_2D,g->shadow_tex,0);{GLenum none=GL_NONE;glDrawBuffers(1,&none);}glReadBuffer(GL_NONE);if(glCheckFramebufferStatus(GL_FRAMEBUFFER)!=GL_FRAMEBUFFER_COMPLETE)LOGE("Shadow target incomplete");glBindTexture(GL_TEXTURE_2D,0);}
            snap=half*2.0f/SIZE;for(a=0;a<3;a++){pos[a]=roundf(c->body.feet[a]/snap)*snap+sun[a]*20000.0f;fwd[a]=-sun[a];}
            cross3(fwd,zup,side);normalize3(side);cross3(side,fwd,up);
            view[0]=side[0];view[4]=side[1];view[8]=side[2];view[12]=-dot3(side,pos);view[1]=up[0];view[5]=up[1];view[9]=up[2];view[13]=-dot3(up,pos);view[2]=-fwd[0];view[6]=-fwd[1];view[10]=-fwd[2];view[14]=dot3(fwd,pos);view[15]=1;
            proj[0]=proj[5]=1.0f/half;proj[10]=-2.0f/40000.0f;proj[14]=-1.0f;proj[15]=1;multiply4(shadow_matrix,proj,view);
            glBindFramebuffer(GL_FRAMEBUFFER,g->shadow_fbo);glViewport(0,0,SIZE,SIZE);glClear(GL_DEPTH_BUFFER_BIT);glEnable(GL_POLYGON_OFFSET_FILL);glPolygonOffset(2.0f,4.0f);
            glUseProgram(g->program);opem_room_lighting_upload(&g->room_lights,0);glUniform1i(glGetUniformLocation(g->program,"room_shadow_on"),0);glUniform1i(glGetUniformLocation(g->program,"room_shadow_map"),3);glUniformMatrix4fv(g->matrix_location,1,GL_FALSE,shadow_matrix);glUniform1f(glGetUniformLocation(g->program,"alpha_cut"),.5f);
            oa_stream_draw(active_stream,shadow_matrix,g->has_texture_location,g->sampler_location,c->body.feet,half*1.5f);
            if(c->collision_ready)oa_character_gpu_draw(&g->character,&c->character,shadow_matrix,0,0.f);if(c->foe_ready)oa_character_gpu_draw(&g->foe,&c->foe,shadow_matrix,0,.5f);
            glDisable(GL_POLYGON_OFFSET_FILL);glBindFramebuffer(GL_FRAMEBUFFER,0);glViewport(0,0,width,height);shadow_on=1;}
"""),
 ('glUniform1f(glGetUniformLocation(g->program,"alpha_cut"),g->room_lights.outdoor?.5f:0.f);', 'glUniform1f(glGetUniformLocation(g->program,"alpha_cut"),g->room_lights.outdoor?.5f:0.f);glUniform1i(glGetUniformLocation(g->program,"room_shadow_map"),3);glUniform1i(glGetUniformLocation(g->program,"room_shadow_on"),shadow_on);if(shadow_on){glUniformMatrix4fv(glGetUniformLocation(g->program,"room_shadow_matrix"),1,GL_FALSE,shadow_matrix);glActiveTexture(GL_TEXTURE3);glBindTexture(GL_TEXTURE_2D,g->shadow_tex);glActiveTexture(GL_TEXTURE0);}'),
 ("        if(prof.skip&2){}else if(g->materials.ready&&!scene_material_renderer_v09_draw(", "        if(prof.skip&2){}else if(active_stream)oa_stream_draw(active_stream,matrix,g->has_texture_location,g->sampler_location,eye,0);else if(g->materials.ready&&!scene_material_renderer_v09_draw("),
 ("        if(!g->materials.ready&&!(prof.skip&2)){glUniform1i(g->has_texture_location,0);", "        if(!active_stream&&!g->materials.ready&&!(prof.skip&2)){glUniform1i(g->has_texture_location,0);"),
 ('     if(prof.on){int64_t gap=', '     if(prof.on&&active_stream&&prof.frames==239){oa_stream_stats st;oa_stream_get_stats(active_stream,&st);LOGI("STREAM cells=%u/%u draws=%u tris=%u gpu_mb=%.0f cpu_mb=%.0f textures=%u queued=%u update_worst_ms=%.2f",st.cells_drawn,st.cells,st.draws,st.triangles,st.gpu_mb,st.cpu_mb,st.textures,st.queued,st.upload_worst_ms);}\n     if(prof.on){int64_t gap='),
 # World loading
 ("    const float *arrive=c->spawn_hint;char error[256]=\"mesh load failed\";opem_collision_stats stats;amalur_scene_mesh collision={0};\n", "    const float *arrive=c->spawn_hint;char error[256]=\"mesh load failed\";opem_collision_stats stats;amalur_scene_mesh collision={0};\n    oa_stream_close(active_stream);active_stream=NULL;\n"),
 ('    if(!mesh_load(manager,world?"town_scene.bin":"scene.bin",mesh)){LOGE("World %d scene unavailable",world);return;}\n', """    if(world)active_stream=oa_stream_open(manager);
    if(active_stream){const float *from=arrive?arrive:oa_doors[1];oa_stream_bounds(active_stream,c->center,&c->radius);c->distance=c->radius*2.5f;
        c->world=oa_stream_collision_now(active_stream,from,error,sizeof(error));
        if(c->world){opem_collision_get_stats(c->world,&stats);LOGI("World %d streamed collision triangles=%u",world,stats.triangles);c->spawn_hint=arrive;exploration_reset(c);}else LOGE("World %d collision unavailable: %s",world,error);}
    else{
    if(!mesh_load(manager,world?"town_scene.bin":"scene.bin",mesh)){LOGE("World %d scene unavailable",world);return;}
"""),
 ('    materials_load(manager,mesh,materials,world?"town_materials.bin":"scene_materials.bin",world?AMALUR_TOWN_SHA256:AMALUR_SCENE_SHA256);\n', '    materials_load(manager,mesh,materials,world?"town_materials.bin":"scene_materials.bin",world?AMALUR_TOWN_SHA256:AMALUR_SCENE_SHA256);\n    }\n'),
 # Frame
 ("                if(playing)oa_npcs_update(&c.npcs,dt);\n", """                if(active_stream){opem_collision_world *next_world=oa_stream_collision_poll(active_stream,c.body.feet);if(next_world){opem_collision_destroy(c.world);c.world=next_world;}}
                if(prof.walk&&playing)movement.move_y=1.f;
                /* Test aid: debug.opem.tour flies the player in a wide loop to force streaming. */
                if(prof.tour&&playing&&active_stream&&c.collision_ready){static float angle;const float *door=oa_doors[1];float R=32000.f,dir[3]={0,0,-1},top[3],hit=0;angle+=dt*(float)prof.tour/R;c.body.feet[0]=door[0]+R*(cosf(angle)-1.f);c.body.feet[1]=door[1]+R*sinf(angle);top[0]=c.body.feet[0];top[1]=c.body.feet[1];top[2]=c.body.feet[2]+3000.f;c.walk_yaw=angle+1.5708f;if(opem_collision_ray(c.world,top,dir,8000.f,&hit)&&hit<8000.f)c.body.feet[2]=top[2]-hit;memcpy(c.character.feet,c.body.feet,sizeof(c.body.feet));c.character.facing=c.walk_yaw;oa_character_pose(&c.character);}
                if(playing)oa_npcs_update(&c.npcs,dt);
"""),
 ("if(focused&&!interaction.window_open&&playing)exploration_update(&c,&movement,dt);", "if(prof.tour&&active_stream&&playing){movement.look_dx=movement.look_dy=0;}else if(focused&&!interaction.window_open&&playing)exploration_update(&c,&movement,dt);"),
 ("    opem_android_scripts_stop(realm);\n", "    oa_stream_close(active_stream);active_stream=NULL;\n    opem_android_scripts_stop(realm);\n"),
])
for f, t in pending:
    f.write_bytes(t.encode("utf-8"))
print("patched", len(pending))
