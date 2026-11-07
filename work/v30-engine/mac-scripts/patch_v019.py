"""Add the Gorhart outdoor world and door switching, version 0.19.0."""
import json, shutil
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
host = root / "work/v19-host"
town = root / "work/v20-town"


def edit(name, pairs):
    p = host / name
    t = p.read_bytes().decode("utf-8")
    for old, new in pairs:
        if t.count(old) != 1:
            raise SystemExit("%s: expected one match for %r, found %d" % (name, old[:100], t.count(old)))
        t = t.replace(old, new)
    p.write_bytes(t.encode("utf-8"))


# Validate every edit before writing any file by working on copies first.
backup = root / "work/v20-char/host-before-v019"
backup.mkdir(exist_ok=True)
for n in ("android_scene.c", "room_lighting.c", "room_lighting.h", "oa_character_gl.c", "oa_character_gl.h", "exploration_overlay.c", "exploration_overlay.h", "AndroidManifest.xml", "CMakeLists.txt", "package_android.py"):
    shutil.copy2(host / n, backup / n)
shutil.copy2(town / "town_environment.inc", host / "town_environment.inc")
sha = json.loads((town / "town-receipt.json").read_text())["scene_sha256"]
(host / "town_identity.h").write_text('#ifndef OA_TOWN_IDENTITY_H\n#define OA_TOWN_IDENTITY_H\n#define AMALUR_TOWN_SHA256 "%s"\n#endif\n' % sha, encoding="utf-8", newline="\n")

edit("room_lighting.h", [
 ("GLuint cube,lut;} opem_room_lighting;", "GLuint cube,lut;int outdoor;} opem_room_lighting;"),
 ("int opem_room_lighting_open(opem_room_lighting *,GLuint program);", "int opem_room_lighting_open(opem_room_lighting *,GLuint program,int outdoor);"),
])
edit("room_lighting.c", [
 ('#include "room_environment.inc"', '#include "room_environment.inc"\n#include "town_environment.inc"'),
 ("int opem_room_lighting_open(opem_room_lighting *s,GLuint program){", "int opem_room_lighting_open(opem_room_lighting *s,GLuint program,int outdoor){\n s->outdoor=outdoor;"),
 ("GL_RGBA,GL_UNSIGNED_BYTE,opem_env_cube[f]);", "GL_RGBA,GL_UNSIGNED_BYTE,outdoor?opem_town_cube[f]:opem_env_cube[f]);"),
 ("GL_RGBA,GL_UNSIGNED_BYTE,opem_env_lut);", "GL_RGBA,GL_UNSIGNED_BYTE,outdoor?opem_town_lut:opem_env_lut);"),
 ("glUniform1i(s->number,OPEM_ROOM_LIGHT_COUNT);", "glUniform1i(s->number,s->outdoor?0:OPEM_ROOM_LIGHT_COUNT);"),
 ("glUniform3fv(s->sun_color,1,opem_env_sun_color);glUniform3fv(s->sun_direction,1,opem_env_sun_direction);glUniform4fv(s->shadow_color,1,opem_env_shadow_color);",
  "glUniform3fv(s->sun_color,1,s->outdoor?opem_town_sun_color:opem_env_sun_color);glUniform3fv(s->sun_direction,1,s->outdoor?opem_town_sun_direction:opem_env_sun_direction);glUniform4fv(s->shadow_color,1,s->outdoor?opem_town_shadow_color:opem_env_shadow_color);"),
])
edit("oa_character_gl.h", [("int oa_character_gpu_open(oa_character_gpu *g,const oa_character *c);", "int oa_character_gpu_open(oa_character_gpu *g,const oa_character *c,int outdoor);")])
edit("oa_character_gl.c", [
 ("int oa_character_gpu_open(oa_character_gpu *g,const oa_character *c){", "int oa_character_gpu_open(oa_character_gpu *g,const oa_character *c,int outdoor){"),
 ("!opem_room_lighting_open(&g->lights,g->program)", "!opem_room_lighting_open(&g->lights,g->program,outdoor)"),
])
edit("exploration_overlay.h", [("const oa_interaction *interaction,int room_lighting);", "const oa_interaction *interaction,int room_lighting,const char *door_prompt);")])
edit("exploration_overlay.c", [
 ("const oa_interaction *interaction,int room_lighting){", "const oa_interaction *interaction,int room_lighting,const char *door_prompt){"),
 ('text(o,w*.5f-148*s,h-94*s,2*s,"ALCHEMY - INTERACT",white);}', 'text(o,w*.5f-148*s,h-94*s,2*s,"ALCHEMY - INTERACT",white);}\nelse if(door_prompt){rect(o,w*.5f-160*s,h-112*s,320*s,52*s,dark);text(o,w*.5f-148*s,h-94*s,2*s,door_prompt,white);}'),
])
edit("android_scene.c", [
 ('#include "oa_character_gl.h"\n', '''#include "oa_character_gl.h"
#include "town_identity.h"
#include <sys/system_properties.h>
/* Door positions come from int_dal_gorhart_alchemistshop_entrance and _exit object records.
 * World 0 is the shop, world 1 is Gorhart. Prompt radius is authored. */
static const float oa_doors[2][3]={{-342.4f,-139.6f,0.0f},{1575.1f,-62759.2f,5152.1f}};
static const char *const oa_door_prompts[2]={"EXIT - INTERACT","ENTER SHOP"};
'''),
 ("    float walk_yaw,walk_pitch,boom;\n", "    float walk_yaw,walk_pitch,boom;\n    const float *spawn_hint;\n"),
 ("const scene_materials_v09 *materials,const oa_character *character){", "const scene_materials_v09 *materials,const oa_character *character,int outdoor){"),
 ("if(!opem_room_lighting_open(&g->room_lights,g->program)){", "if(!opem_room_lighting_open(&g->room_lights,g->program,outdoor)){"),
 ("oa_character_gpu_open(&g->character,character)", "oa_character_gpu_open(&g->character,character,outdoor)"),
 ("const oa_interaction *interaction,int room_lighting){\n    EGLint width,height;", "const oa_interaction *interaction,int room_lighting,const char *door_prompt){\n    EGLint width,height;"),
 ("glClearColor(mesh->vertices?0.055f:0.17f,0.065f,0.08f,1);", "if(g->room_lights.outdoor)glClearColor(.46f,.60f,.76f,1);else glClearColor(mesh->vertices?0.055f:0.17f,0.065f,0.08f,1);"),
 ("c->walking,c->collision_ready,interaction,room_lighting);", "c->walking,c->collision_ready,interaction,room_lighting,door_prompt);"),
 ("static void materials_load(AAssetManager *manager,const amalur_scene_mesh *mesh,scene_materials_v09 *materials){\n    const char *hex=AMALUR_SCENE_SHA256;", "static void materials_load(AAssetManager *manager,const amalur_scene_mesh *mesh,scene_materials_v09 *materials,const char *asset_name,const char *hex){\n   "),
 ('asset=AAssetManager_open(manager,"scene_materials.bin",AASSET_MODE_STREAMING);', "asset=AAssetManager_open(manager,asset_name,AASSET_MODE_STREAMING);"),
 ("const float *hint=oa_workbench_spawn_hint;", "const float *hint=c->spawn_hint?c->spawn_hint:oa_workbench_spawn_hint;"),
 ("static void *worker_main(void *argument){", '''/* Replaces scene, materials and collision. The caller reopens graphics afterwards. */
static void world_load(AAssetManager *manager,int world,amalur_scene_mesh *mesh,scene_materials_v09 *materials,camera *c){
    const float *arrive=c->spawn_hint;char error[256];opem_collision_stats stats;amalur_scene_mesh collision={0};
    amalur_scene_mesh_clear(mesh);scene_materials_v09_free(materials);memset(materials,0,sizeof(*materials));opem_collision_destroy(c->world);c->world=NULL;c->collision_ready=0;c->walking=0;
    if(!mesh_load(manager,world?"town_scene.bin":"scene.bin",mesh)){LOGE("World %d scene unavailable",world);return;}
    {double radius2=0;int i;for(i=0;i<3;i++){double d=(double)mesh->bounds_max[i]-mesh->bounds_min[i];c->center[i]=(float)(((double)mesh->bounds_min[i]+mesh->bounds_max[i])*0.5);radius2+=d*d;}c->radius=(float)(sqrt(radius2)*0.5);c->distance=c->radius*2.5f;}
    if(mesh_load(manager,world?"town_collision.bin":"collision.bin",&collision)&&opem_collision_create(&c->world,collision.vertices,collision.vertex_count,9,error,sizeof(error))){opem_collision_get_stats(c->world,&stats);LOGI("World %d collision triangles=%u",world,stats.triangles);c->spawn_hint=arrive;exploration_reset(c);}
    else LOGE("World %d collision unavailable",world);
    amalur_scene_mesh_clear(&collision);
    materials_load(manager,mesh,materials,world?"town_materials.bin":"scene_materials.bin",world?AMALUR_TOWN_SHA256:AMALUR_SCENE_SHA256);
    LOGI("World switched to %s ready=%d",world?"gorhart":"shop",c->collision_ready);
}
static void *worker_main(void *argument){'''),
 ("    input_host inputs={0};amalur_runtime *realm=NULL;", "    int world=0,world_request=-1;const char *door_prompt=NULL;\n    input_host inputs={0};amalur_runtime *realm=NULL;"),
 ("        materials_load(s->activity->assetManager,&mesh,&materials);\n", '        materials_load(s->activity->assetManager,&mesh,&materials,"scene_materials.bin",AMALUR_SCENE_SHA256);\n'),
 ("graphics_open(&g,s->active_window,&mesh,&materials,&c.character);", "graphics_open(&g,s->active_window,&mesh,&materials,&c.character,world);"),
 ("        oa_android_start(&interaction,realm,s->activity->assetManager,inventory_path);\n", '''        oa_android_start(&interaction,realm,s->activity->assetManager,inventory_path);
        /* Test aid: adb shell setprop debug.opem.world town opens Gorhart without walking to the door. */
        {char prop[PROP_VALUE_MAX]={0};if(__system_property_get("debug.opem.world",prop)>0&&!strcmp(prop,"town")){world_request=1;c.spawn_hint=oa_doors[1];}}
'''),
 ("if(c.walking&&c.collision_ready&&interaction.ready){", "if(world==0&&c.walking&&c.collision_ready&&interaction.ready){"),
 ("                    if(movement.interact_requested){char error[256];movement.interact_requested=0;if(interaction.selected.generation){", '''                    door_prompt=NULL;
                    if(c.walking&&c.collision_ready&&world_request<0){const float *door=oa_doors[world];float dx=c.body.feet[0]-door[0],dy=c.body.feet[1]-door[1],dz=c.body.feet[2]-door[2];
                        if(dx*dx+dy*dy<260.f*260.f&&fabsf(dz)<220.f&&!interaction.selected.generation){door_prompt=oa_door_prompts[world];
                            if(movement.interact_requested){movement.interact_requested=0;world_request=!world;c.spawn_hint=oa_doors[world_request];}}}
                    if(movement.interact_requested){char error[256];movement.interact_requested=0;if(interaction.selected.generation){'''),
 ("                if(observed_lighting_mode!=room_lighting||!lighting_started_ms){", '''                if(world_request>=0){int next=world_request;world_request=-1;door_prompt=NULL;
                    pthread_mutex_lock(&s->mutex);graphics_close(&g);world_load(s->activity->assetManager,next,&mesh,&materials,&c);world=next;
                    if(s->active_window)graphics_open(&g,s->active_window,&mesh,&materials,&c.character,world);pthread_mutex_unlock(&s->mutex);
                    if(c.collision_ready){c.character.facing=c.walk_yaw;memcpy(c.character.feet,c.body.feet,sizeof(c.body.feet));oa_character_pose(&c.character);}
                    exploration_input_clear(&movement);last_frame_ms=0;lighting_started_ms=0;
                    if(!g.ready)continue;}
                if(observed_lighting_mode!=room_lighting||!lighting_started_ms){'''),
 ("graphics_draw(&g,&mesh,&materials,&c,&movement,&interaction,room_lighting)", "graphics_draw(&g,&mesh,&materials,&c,&movement,&interaction,room_lighting,door_prompt)"),
])
edit("AndroidManifest.xml", [('android:versionCode="19" android:versionName="0.18.0"', 'android:versionCode="20" android:versionName="0.19.0"')])
edit("CMakeLists.txt", [("VERSION 0.18.0", "VERSION 0.19.0")])
edit("package_android.py", [
 ("opem-amalur-scene-v0.18-arm64.apk", "opem-amalur-scene-v0.19-arm64.apk"),
 ("files['assets/character.bin']=root/'work/v20-char/character.bin'", "files['assets/character.bin']=root/'work/v20-char/character.bin'\nfor name in ('town_scene.bin','town_materials.bin','town_collision.bin'):files['assets/'+name]=root/'work/v20-town'/name"),
])
print("patched")
