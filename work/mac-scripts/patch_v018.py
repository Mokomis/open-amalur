"""Integrate the skinned character and third-person view into the Android host, version 0.18.0."""
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
host = root / "work/v19-host"


def edit(name, pairs):
    p = host / name
    t = p.read_text(encoding="utf-8")
    for old, new in pairs:
        if t.count(old) != 1:
            raise SystemExit("%s: expected one match for %r, found %d" % (name, old[:90], t.count(old)))
        t = t.replace(old, new)
    p.write_text(t, encoding="utf-8", newline="")


edit("android_scene.c", [
 ('#include "room_lighting_shader.h"\n', '#include "room_lighting_shader.h"\n#include "oa_character_gl.h"\n'),
 ('    opem_room_lighting room_lights;\n} graphics;', '    opem_room_lighting room_lights;\n    oa_character_gpu character;\n} graphics;'),
 ('    float walk_yaw,walk_pitch;\n', '    float walk_yaw,walk_pitch,boom;\n    oa_character character;\n'),
 ('        eye[0]=c->body.feet[0];eye[1]=c->body.feet[1];eye[2]=c->body.feet[2]+c->body_config.height*.9f;\n        forward[0]=cosf(c->walk_pitch)*cosf(c->walk_yaw);forward[1]=cosf(c->walk_pitch)*sinf(c->walk_yaw);forward[2]=sinf(c->walk_pitch);\n',
  '        forward[0]=cosf(c->walk_pitch)*cosf(c->walk_yaw);forward[1]=cosf(c->walk_pitch)*sinf(c->walk_yaw);forward[2]=sinf(c->walk_pitch);\n        /* Authored third-person boom behind the character; c->boom is collision-limited. */\n        eye[0]=c->body.feet[0]-forward[0]*c->boom;eye[1]=c->body.feet[1]-forward[1]*c->boom;eye[2]=c->body.feet[2]+OA_CAMERA_PIVOT-forward[2]*c->boom;\n'),
 ('static void camera_matrix(const camera *c,float aspect,float output[16]){', '#define OA_CAMERA_PIVOT 150.0f\n#define OA_CAMERA_BOOM 240.0f\nstatic void camera_matrix(const camera *c,float aspect,float output[16]){'),
 ('        opem_room_lighting_close(&g->room_lights);if(g->program)glDeleteProgram(g->program);', '        oa_character_gpu_close(&g->character);opem_room_lighting_close(&g->room_lights);if(g->program)glDeleteProgram(g->program);'),
 ('static int graphics_open(graphics *g,ANativeWindow *window,const amalur_scene_mesh *mesh,const scene_materials_v09 *materials){', 'static int graphics_open(graphics *g,ANativeWindow *window,const amalur_scene_mesh *mesh,const scene_materials_v09 *materials,const oa_character *character){'),
 ('    if(!exploration_overlay_open(&g->overlay)){', '    if(character->ready){if(oa_character_gpu_open(&g->character,character))LOGI("Character GPU ready parts=%u textures=%u clips=%u",character->part_count,character->texture_count,character->clip_count);else LOGE("Character unavailable; continuing without it");}\n    if(!exploration_overlay_open(&g->overlay)){'),
 ('        if(!g->materials.ready){glUniform1i(g->has_texture_location,0);glDrawArrays(GL_TRIANGLES,0,(GLsizei)mesh->vertex_count);}glBindVertexArray(0);}',
  '        if(!g->materials.ready){glUniform1i(g->has_texture_location,0);glDrawArrays(GL_TRIANGLES,0,(GLsizei)mesh->vertex_count);}glBindVertexArray(0);\n        if(c->collision_ready)oa_character_gpu_draw(&g->character,&c->character,matrix,room_lighting);}'),
 ('static void materials_load(AAssetManager *manager,', '''static void character_load(AAssetManager *manager,oa_character *character){
    AAsset *asset=AAssetManager_open(manager,"character.bin",AASSET_MODE_BUFFER);uint8_t *bytes;off_t size;char error[128];
    if(!asset){LOGE("Character asset missing");return;}
    size=AAsset_getLength(asset);bytes=size>0?(uint8_t*)malloc((size_t)size):NULL;
    if(bytes&&AAsset_read(asset,bytes,(size_t)size)==size&&oa_character_parse(character,bytes,(size_t)size,error,sizeof(error)))LOGI("Character asset loaded bytes=%lld joints=%u",(long long)size,character->joints);
    else{LOGE("Character asset rejected: %s",bytes?error:"allocation");free(bytes);}
    AAsset_close(asset);
}
static void materials_load(AAssetManager *manager,'''),
 ('        c->collision_ready=1;c->walking=1;c->walk_yaw=1.5707963268f;c->walk_pitch=-.2f;', '        c->collision_ready=1;c->walking=1;c->walk_yaw=1.5707963268f;c->walk_pitch=-.2f;c->boom=OA_CAMERA_BOOM;c->character.facing=c->walk_yaw;memcpy(c->character.feet,c->body.feet,sizeof(c->body.feet));'),
 ('        }else if(c->body.recovered_last_step)++c->recovery_count;\n', '''        }else if(c->body.recovered_last_step)++c->recovery_count;
        if(c->collision_ready)character_update(c,right,forward,dt);
'''),
 ('static void exploration_update(camera *c,exploration_input *input,float dt){', '''static void character_update(camera *c,float right,float forward,float dt){
    float speed=sqrtf(right*right+forward*forward),pivot[3],back[3],hit=0,want=OA_CAMERA_BOOM;
    if(speed>1)speed=1;
    if(speed>.05f){float vx=cosf(c->walk_yaw)*forward+sinf(c->walk_yaw)*right,vy=sinf(c->walk_yaw)*forward-cosf(c->walk_yaw)*right,target=atan2f(vy,vx),turn=remainderf(target-c->character.facing,6.283185307f),step=dt*12.0f;
        c->character.facing=remainderf(c->character.facing+(turn>step?step:turn<-step?-step:turn),6.283185307f);}
    memcpy(c->character.feet,c->body.feet,sizeof(c->body.feet));
    oa_character_animate(&c->character,speed,speed*c->body_config.max_speed,dt);oa_character_pose(&c->character);
    pivot[0]=c->body.feet[0];pivot[1]=c->body.feet[1];pivot[2]=c->body.feet[2]+OA_CAMERA_PIVOT;
    back[0]=-cosf(c->walk_pitch)*cosf(c->walk_yaw);back[1]=-cosf(c->walk_pitch)*sinf(c->walk_yaw);back[2]=-sinf(c->walk_pitch);
    if(opem_collision_ray(c->world,pivot,back,OA_CAMERA_BOOM,&hit)&&hit<OA_CAMERA_BOOM)want=hit-12.0f;
    if(want<25.0f)want=25.0f;
    c->boom=want<c->boom?want:c->boom+(want-c->boom)*(dt*4.0f>1?1:dt*4.0f);
}
static void exploration_update(camera *c,exploration_input *input,float dt){'''),
 ('    c.body_config.require_ceiling=0;\n', '    c.body_config.require_ceiling=0;\n    /* Authored third-person run speed, matched to the run clip; not a recovered native value. */\n    c.body_config.max_speed=420.0f;\n'),
 ('        materials_load(s->activity->assetManager,&mesh,&materials);\n', '        materials_load(s->activity->assetManager,&mesh,&materials);\n        character_load(s->activity->assetManager,&c.character);\n        if(c.collision_ready&&c.character.ready){c.character.facing=c.walk_yaw;memcpy(c.character.feet,c.body.feet,sizeof(c.body.feet));}\n'),
 ('graphics_open(&g,s->active_window,&mesh,&materials);', 'graphics_open(&g,s->active_window,&mesh,&materials,&c.character);'),
 ('    opem_collision_destroy(c.world);\n', '    oa_character_free(&c.character);\n    opem_collision_destroy(c.world);\n'),
])
edit("android_scene.cmake", [("android_scene.c room_lighting.c ", "android_scene.c room_lighting.c oa_character.c oa_character_gl.c ")])
edit("CMakeLists.txt", [("VERSION 0.17.0", "VERSION 0.18.0"), ("add_executable(amalur-exploration-input-test ", "add_executable(oa-character-test oa_character_test.c oa_character.c)\nadd_executable(amalur-exploration-input-test ")])
edit("AndroidManifest.xml", [('android:versionCode="18" android:versionName="0.17.0"', 'android:versionCode="19" android:versionName="0.18.0"')])
edit("build_validate.cmd", [
 ("--target amalur-exploration-input-test --parallel 8", "--target amalur-exploration-input-test oa-character-test --parallel 8"),
 ("work\\v19-host\\build-windows\\amalur-exploration-input-test.exe > outputs\\scene-v19\\input-tests.txt 2>&1\r\nif errorlevel 1 exit /b %errorlevel%\r\n",
  "work\\v19-host\\build-windows\\amalur-exploration-input-test.exe > outputs\\scene-v19\\input-tests.txt 2>&1\r\nif errorlevel 1 exit /b %errorlevel%\r\nwork\\v19-host\\build-windows\\oa-character-test.exe work\\v20-char\\character.bin > outputs\\scene-v19\\character-tests.txt 2>&1\r\nif errorlevel 1 exit /b %errorlevel%\r\n"),
])
edit("package_android.py", [
 ("opem-amalur-scene-v0.17-arm64.apk", "opem-amalur-scene-v0.18-arm64.apk"),
 ("files['assets/collision.bin']=root/'outputs/scene-v17/collision.bin'\n", "files['assets/collision.bin']=root/'outputs/scene-v17/collision.bin'\nfiles['assets/character.bin']=root/'work/v20-char/character.bin'\n"),
])
print("patched")
