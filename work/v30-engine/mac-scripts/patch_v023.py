"""Version 0.23.0: game sky in Gorhart."""
from pathlib import Path
host = Path.home() / "Documents/Opem Amalur/work/v19-host"


def edit(name, pairs):
    f = host / name
    t = f.read_bytes().decode("utf-8")
    for old, new in pairs:
        if t.count(old) != 1:
            raise SystemExit("%s: expected one match for %r, found %d" % (name, old[:90], t.count(old)))
        t = t.replace(old, new)
    f.write_bytes(t.encode("utf-8"))


edit("android_scene.cmake", [("oa_character.c oa_npc.c oa_combat.c oa_character_gl.c ", "oa_character.c oa_npc.c oa_combat.c oa_character_gl.c oa_sky.c ")])
edit("CMakeLists.txt", [("VERSION 0.22.0", "VERSION 0.23.0")])
edit("AndroidManifest.xml", [('android:versionCode="23" android:versionName="0.22.0"', 'android:versionCode="24" android:versionName="0.23.0"')])
edit("package_android.py", [
 ("opem-amalur-scene-v0.22-arm64.apk", "opem-amalur-scene-v0.23-arm64.apk"),
 ("'town_npcs.bin','town_enemy.bin')", "'town_npcs.bin','town_enemy.bin','town_sky.bin')"),
])
edit("android_scene.c", [
 ('#include "oa_combat.h"\n', '#include "oa_combat.h"\n#include "oa_sky.h"\n'),
 ("    oa_character_gpu foe;\n} graphics;", "    oa_character_gpu foe;\n    oa_sky sky;\n} graphics;"),
 ("    int foe_ready;\n", "    int foe_ready;\n    uint8_t *sky_bytes;\n    size_t sky_size;\n"),
 ("static void camera_matrix(const camera *c,float aspect,float output[16]){", "static void camera_matrix(const camera *c,float aspect,float output[16],float eye_out[3]){"),
 ("    multiply4(output,projection,view);\n}", "    multiply4(output,projection,view);\n    memcpy(eye_out,eye,sizeof(eye));\n}"),
 ("if(g->foe.program)oa_character_gpu_close(&g->foe);", "oa_sky_close(&g->sky);if(g->foe.program)oa_character_gpu_close(&g->foe);"),
 ("const oa_character *foe,int outdoor){", "const oa_character *foe,const uint8_t *sky_bytes,size_t sky_size,int outdoor){"),
 ('''    if(foe->ready&&!oa_character_gpu_open''', '''    if(outdoor&&sky_bytes&&!oa_sky_open(&g->sky,sky_bytes,sky_size))LOGE("Sky unavailable; flat color remains");
    if(foe->ready&&!oa_character_gpu_open'''),
 ("if(mesh->vertices){float matrix[16];camera_matrix(c,(float)width/(float)height,matrix);", "if(mesh->vertices){float matrix[16],eye[3];camera_matrix(c,(float)width/(float)height,matrix,eye);\n        if(g->sky.ready)oa_sky_draw(&g->sky,matrix,eye,c->radius*8.0f,(float)(monotonic_ms()%3600000)*.001f,g->room_lights.lut);"),
 ("    oa_npcs_free(&c->npcs);\n    if(c->foe.bytes)oa_character_free(&c->foe);\n", '''    oa_npcs_free(&c->npcs);
    free(c->sky_bytes);c->sky_bytes=NULL;c->sky_size=0;
    if(world){AAsset *asset=AAssetManager_open(manager,"town_sky.bin",AASSET_MODE_BUFFER);
        if(asset){size_t size=(size_t)AAsset_getLength64(asset);uint8_t *bytes=(uint8_t*)malloc(size);if(bytes&&AAsset_read(asset,bytes,size)==(int)size){c->sky_bytes=bytes;c->sky_size=size;}else free(bytes);AAsset_close(asset);}
        else LOGE("Sky asset missing");}
    if(c->foe.bytes)oa_character_free(&c->foe);
'''),
 ("&c.character,&c.npcs,&c.foe,world);pthread_mutex_unlock(&s->mutex);", "&c.character,&c.npcs,&c.foe,c.sky_bytes,c.sky_size,world);pthread_mutex_unlock(&s->mutex);"),
 ("&c.character,&c.npcs,&c.foe,world);}", "&c.character,&c.npcs,&c.foe,c.sky_bytes,c.sky_size,world);}"),
 ("    oa_npcs_free(&c.npcs);\n    if(c.foe.bytes)oa_character_free(&c.foe);\n", "    oa_npcs_free(&c.npcs);\n    free(c.sky_bytes);\n    if(c.foe.bytes)oa_character_free(&c.foe);\n"),
])
print("patched")
