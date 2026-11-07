"""Version 0.21.0: townspeople in Gorhart, drawn from town_npcs.bin."""
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
host = root / "work/v19-host"
wc = root / "work/v20-char"


def edit_text(t, name, pairs):
    for old, new in pairs:
        if t.count(old) != 1:
            raise SystemExit("%s: expected one match for %r, found %d" % (name, old[:90], t.count(old)))
        t = t.replace(old, new)
    return t


def edit(name, pairs):
    f = host / name
    f.write_bytes(edit_text(f.read_bytes().decode("utf-8"), name, pairs).encode("utf-8"))


p = wc / "build_npcs.py"
p.write_text(edit_text(p.read_text(encoding="utf-8"), "build_npcs", [
 ('''    result = None
    for tid, name in order:
        best = decode_best(tid)
''', '''    result = None
    if not any(r[1].lower().endswith("_d") for r in refs) and alpha:
        # Hair and beards carry only a shape mask; the game tints them at runtime. Neutral brown is an authored stand-in.
        mask = decode_best(alpha)
        if mask:
            mw, mh, mr = mask
            o = bytearray(b"\\x3a\\x28\\x1c\\xff" * (mw * mh))
            o[3::4] = mr[0::4]
            result = (mw, mh, bytes(o), "tinted mask")
            texture_cache[mid] = result
            return result
    for tid, name in order:
        best = decode_best(tid)
'''),
 ('''            mid = mats[ai] if ai < len(mats) else (mats[0] if mats else 0)
''', '''            mid = mats[ai] if ai < len(mats) else (mats[0] if mats else 0)
            if re.search(r"eye_shadow|face_acc|eyelash", syms["material"].get(str(mid), "")):
                continue  # Overlay decals need blending the renderer does not have yet.
'''),
 ('if not parts or len(parts) > 16 or len(textures) > 16:', 'if not parts or len(parts) > 24 or len(textures) > 16:'),
]), encoding="utf-8", newline="\n")

(host / "oa_npc.h").write_text('''#ifndef OA_NPC_H
#define OA_NPC_H
/* Townspeople placed from their object records. Standing idle only; no behaviour yet. */
#include "oa_character.h"
enum{OA_NPC_MAX=16};
typedef struct oa_npcs{unsigned count;oa_character people[OA_NPC_MAX];}oa_npcs;
/* Copies what it needs; bytes remain owned by the caller. */
int oa_npcs_parse(oa_npcs *n,const uint8_t *bytes,size_t size,char *error,size_t error_size);
void oa_npcs_free(oa_npcs *n);
void oa_npcs_update(oa_npcs *n,float dt);
#endif
''', encoding="utf-8", newline="\n")
(host / "oa_npc.c").write_text('''#include "oa_npc.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int oa_npcs_parse(oa_npcs *n,const uint8_t *bytes,size_t size,char *error,size_t error_size){
 size_t at=12;uint32_t count,i;memset(n,0,sizeof(*n));
 if(size<12||memcmp(bytes,"OANPCS01",8)){snprintf(error,error_size,"people asset header invalid");return 0;}
 memcpy(&count,bytes+8,4);if(count>OA_NPC_MAX){snprintf(error,error_size,"too many people");return 0;}
 for(i=0;i<count;i++){float place[4];uint32_t length;uint8_t *copy;oa_character *c=n->people+n->count;
  if(size-at<20){snprintf(error,error_size,"people asset truncated");oa_npcs_free(n);return 0;}
  memcpy(place,bytes+at,16);memcpy(&length,bytes+at+16,4);at+=20;
  if(length>size-at){snprintf(error,error_size,"people asset truncated");oa_npcs_free(n);return 0;}
  copy=(uint8_t*)malloc(length);if(!copy){snprintf(error,error_size,"people allocation failed");oa_npcs_free(n);return 0;}
  memcpy(copy,bytes+at,length);at+=length;
  if(!oa_character_parse(c,copy,length,error,error_size)){free(copy);oa_npcs_free(n);return 0;}
  memcpy(c->feet,place,12);c->facing=place[3];
  /* Spread start times so the crowd does not breathe in unison. */
  {const oa_char_clip *k=c->clips;c->time[0]=(float)((i*37u)%(k->frames-1))/k->fps;}
  oa_character_pose(c);n->count++;}
 if(at!=size){snprintf(error,error_size,"people asset has trailing bytes");oa_npcs_free(n);return 0;}
 return 1;
}
void oa_npcs_free(oa_npcs *n){unsigned i;for(i=0;i<n->count;i++)oa_character_free(n->people+i);n->count=0;}
void oa_npcs_update(oa_npcs *n,float dt){unsigned i;for(i=0;i<n->count;i++){oa_character_animate(n->people+i,0,0,dt);oa_character_pose(n->people+i);}}
''', encoding="utf-8", newline="\n")

edit("oa_character.h", [("OA_CHAR_MAX_PARTS=8,OA_CHAR_MAX_TEXTURES=8", "OA_CHAR_MAX_PARTS=24,OA_CHAR_MAX_TEXTURES=16")])
edit("oa_character.c", [
 ("if(!c->ready||c->clip_count<3)return;\n", '''if(!c->ready)return;
 if(c->clip_count<3){const oa_char_clip *k=c->clips;c->time[0]=fmodf(c->time[0]+dt,(float)(k->frames-1)/k->fps);return;}
'''),
])
edit("oa_character_gl.h", [
 ("GLint mvp,bones,has_texture,sampler;", "GLint mvp,bones,has_texture,sampler,alpha_cut;"),
 ("void oa_character_gpu_draw(oa_character_gpu *g,const oa_character *c,const float mvp[16],int room_lighting);", "void oa_character_gpu_draw(oa_character_gpu *g,const oa_character *c,const float mvp[16],int room_lighting,float alpha_cut);"),
])
edit("oa_character_gl.c", [
 ('g->sampler=glGetUniformLocation(g->program,"base_texture");', 'g->sampler=glGetUniformLocation(g->program,"base_texture");g->alpha_cut=glGetUniformLocation(g->program,"alpha_cut");'),
 ("void oa_character_gpu_draw(oa_character_gpu *g,const oa_character *c,const float mvp[16],int room_lighting){", "void oa_character_gpu_draw(oa_character_gpu *g,const oa_character *c,const float mvp[16],int room_lighting,float alpha_cut){"),
 ("glUniform1i(g->sampler,0);\n", "glUniform1i(g->sampler,0);glUniform1f(g->alpha_cut,alpha_cut);\n"),
])
edit("android_scene.cmake", [("oa_character.c oa_character_gl.c ", "oa_character.c oa_npc.c oa_character_gl.c ")])
edit("CMakeLists.txt", [
 ("VERSION 0.20.0", "VERSION 0.21.0"),
 ("add_executable(oa-character-test oa_character_test.c oa_character.c)", "add_executable(oa-character-test oa_character_test.c oa_character.c oa_npc.c)"),
])
edit("oa_character_test.c", [
 ('#include "oa_character.h"\n', '#include "oa_npc.h"\n'),
 ("if(argc!=2)return 2;f=fopen(argv[1]", "if(argc!=3)return 2;f=fopen(argv[1]"),
 ('oa_character_free(&c);printf("character-test: %d checks passed\\n",checks);return 0;', '''oa_character_free(&c);
 {static oa_npcs n;uint8_t *people;f=fopen(argv[2],"rb");if(!f)return 2;fseek(f,0,SEEK_END);n_size_read:n_bytes=ftell(f);rewind(f);people=(uint8_t*)malloc((size_t)n_bytes);if(fread(people,1,(size_t)n_bytes,f)!=(size_t)n_bytes)return 2;fclose(f);
  for(k=0;k<60;k++){size_t cut=(size_t)((uint64_t)n_bytes*k/60);CHECK(!oa_npcs_parse(&n,people,cut,error,sizeof(error)));}
  CHECK(oa_npcs_parse(&n,people,(size_t)n_bytes,error,sizeof(error)));CHECK(n.count>=8);
  for(k=0;k<120;k++)oa_npcs_update(&n,1/60.f);
  for(i=0;i<n.count;i++){float head=n.people[i].world_t[21][2];CHECK(head>120&&head<200);CHECK(n.people[i].feet[2]>4000&&n.people[i].feet[2]<8000);}
  oa_npcs_free(&n);free(people);}
 printf("character-test: %d checks passed\\n",checks);return 0;'''),
 ("oa_character c;char error[128];FILE *f;long n;uint8_t *b,*bad;int checks=0;uint32_t i,k;", "oa_character c;char error[128];FILE *f;long n,n_bytes;uint8_t *b,*bad;int checks=0;uint32_t i,k;"),
])
t = (host / "oa_character_test.c").read_bytes().decode().replace("n_size_read:", "")
(host / "oa_character_test.c").write_bytes(t.encode())
b = (host / "build_validate.cmd").read_bytes().decode()
a = "oa-character-test.exe work\\v20-char\\character.bin >"
assert b.count(a) == 1
(host / "build_validate.cmd").write_bytes(b.replace(a, "oa-character-test.exe work\\v20-char\\character.bin work\\v20-town\\town_npcs.bin >").encode())
edit("android_scene.c", [
 ('#include "oa_character_gl.h"\n', '#include "oa_character_gl.h"\n#include "oa_npc.h"\n'),
 ("    oa_character_gpu character;\n} graphics;", "    oa_character_gpu character;\n    oa_character_gpu people[OA_NPC_MAX];\n} graphics;"),
 ("    oa_character character;\n", "    oa_character character;\n    oa_npcs npcs;\n"),
 ("oa_character_gpu_close(&g->character);opem_room_lighting_close", "{int p;for(p=0;p<OA_NPC_MAX;p++)if(g->people[p].program)oa_character_gpu_close(&g->people[p]);}oa_character_gpu_close(&g->character);opem_room_lighting_close"),
 ("const oa_character *character,int outdoor){", "const oa_character *character,const oa_npcs *npcs,int outdoor){"),
 ("    if(!exploration_overlay_open(&g->overlay)){", '''    {unsigned p;for(p=0;p<npcs->count;p++)if(!oa_character_gpu_open(&g->people[p],npcs->people+p,outdoor))LOGE("Person %u unavailable",p);}
    if(!exploration_overlay_open(&g->overlay)){'''),
 ("if(c->collision_ready)oa_character_gpu_draw(&g->character,&c->character,matrix,room_lighting);}", "if(c->collision_ready)oa_character_gpu_draw(&g->character,&c->character,matrix,room_lighting,0.f);\n        {unsigned p;for(p=0;p<c->npcs.count;p++)oa_character_gpu_draw(&g->people[p],c->npcs.people+p,matrix,room_lighting,.5f);}}"),
 ('''    LOGI("World switched to %s ready=%d",world?"gorhart":"shop",c->collision_ready);''', '''    oa_npcs_free(&c->npcs);
    if(world){AAsset *asset=AAssetManager_open(manager,"town_npcs.bin",AASSET_MODE_BUFFER);
        if(asset){const uint8_t *bytes=(const uint8_t*)AAsset_getBuffer(asset);size_t size=(size_t)AAsset_getLength64(asset);
            if(bytes&&oa_npcs_parse(&c->npcs,bytes,size,error,sizeof(error)))LOGI("Townspeople loaded count=%u",c->npcs.count);else LOGE("Townspeople rejected: %s",bytes?error:"no buffer");AAsset_close(asset);}
        else LOGE("Townspeople asset missing");}
    LOGI("World switched to %s ready=%d",world?"gorhart":"shop",c->collision_ready);'''),
 ("graphics_open(&g,s->active_window,&mesh,&materials,&c.character,world);pthread_mutex_unlock(&s->mutex);", "graphics_open(&g,s->active_window,&mesh,&materials,&c.character,&c.npcs,world);pthread_mutex_unlock(&s->mutex);"),
 ("if(s->active_window){ANativeWindow_acquire(s->active_window);graphics_open(&g,s->active_window,&mesh,&materials,&c.character,world);}", "if(s->active_window){ANativeWindow_acquire(s->active_window);graphics_open(&g,s->active_window,&mesh,&materials,&c.character,&c.npcs,world);}"),
 ("if(focused&&!interaction.window_open)exploration_update(&c,&movement,dt);", "oa_npcs_update(&c.npcs,dt);\n                if(focused&&!interaction.window_open)exploration_update(&c,&movement,dt);"),
 ("    oa_character_free(&c.character);\n", "    oa_npcs_free(&c.npcs);\n    oa_character_free(&c.character);\n"),
])
edit("AndroidManifest.xml", [('android:versionCode="21" android:versionName="0.20.0"', 'android:versionCode="22" android:versionName="0.21.0"')])
edit("package_android.py", [
 ("opem-amalur-scene-v0.20-arm64.apk", "opem-amalur-scene-v0.21-arm64.apk"),
 ("('town_scene.bin','town_materials.bin','town_collision.bin')", "('town_scene.bin','town_materials.bin','town_collision.bin','town_npcs.bin')"),
])
print("patched")
