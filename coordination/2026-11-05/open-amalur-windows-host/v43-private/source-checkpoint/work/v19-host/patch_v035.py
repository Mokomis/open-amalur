import json,struct
from pathlib import Path
R=Path.home()/"Documents/Opem Amalur";r=R/"work/v19-host"
def edit(f,fn):
    s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n");s=fn(s)
    if crlf:s=s.replace("\n","\r\n")
    f.write_bytes(s.encode())
def rep(s,a,b):
    assert a in s,a[:70]
    return s.replace(a,b,1)
def scene(s):
    s=rep(s,"world_programs[4];","world_programs[5];")
    s=rep(s,"{int wi;for(wi=0;wi<4;wi++)if(g->world_programs[wi])","{int wi;for(wi=0;wi<5;wi++)if(g->world_programs[wi])")
    s=rep(s,"{int wi,all=1;for(wi=0;wi<4;wi++){g->world_programs[wi]=","{int wi,all=1;for(wi=0;wi<5;wi++){g->world_programs[wi]=")
    s=rep(s,"for(v=0;v<4;v++){GLuint w=g->world_programs[v];","for(v=0;v<5;v++){GLuint w=g->world_programs[v];")
    return s
edit(r/"android_scene.c",scene)
def ch(s):
    return rep(s," int combat_stance;\n"," int combat_stance;\n /* Human rigs only: the head stays up while the body leans into a run. */\n int level_head;\n")
edit(r/"oa_character.h",ch)
def cc(s):
    s=rep(s," c->bytes=bytes;c->size=size;c->weight[OA_CLIP_IDLE]=1;"," c->level_head=c->joints==64&&c->parents[21]==20&&c->parents[20]==19;\n c->bytes=bytes;c->size=size;c->weight[OA_CLIP_IDLE]=1;")
    s=rep(s,"void oa_character_pose(oa_character *c){\n uint32_t j,i;if(!c->ready)return;","""void oa_character_pose(oa_character *c){
 uint32_t j,i;float level[4]={0,0,0,1};if(!c->ready)return;
 /* Half of the correction at the neck and half at the head. The angles are authored: the game's look layer is not recovered. */
 if(c->level_head){float lean=c->weight[OA_CLIP_WALK]*.16f+c->weight[OA_CLIP_RUN]*.42f;if(c->clip_count>OA_CLIP_COMBAT+2u)lean+=c->weight[OA_CLIP_COMBAT]*.3f+c->weight[OA_CLIP_COMBAT+1]*.4f+c->weight[OA_CLIP_COMBAT+2]*.4f;level[1]=sinf(-lean*.25f);level[3]=cosf(lean*.25f);}""")
    s=rep(s,"else{const int p=c->parents[j];float r[3];qmul(c->world_q[j],c->world_q[p],q);qrot(r,c->world_q[p],t);for(i=0;i<3;i++)c->world_t[j][i]=c->world_t[p][i]+r[i];}}","else{const int p=c->parents[j];float r[3];qmul(c->world_q[j],c->world_q[p],q);qrot(r,c->world_q[p],t);for(i=0;i<3;i++)c->world_t[j][i]=c->world_t[p][i]+r[i];}\n  if(c->level_head&&(j==20||j==21)){float was[4];memcpy(was,c->world_q[j],16);qmul(c->world_q[j],level,was);}}")
    return s
edit(r/"oa_character.c",cc)
def bc(s):
    a=s.index('HEADS = [v for name in');b=s.index("\n",a)
    # The head the zone's own men wear: its neck reaches into the collar. The helmet-slot pieces stop above it.
    return s[:a]+"# The head the zone's own men wear: its neck reaches into the collar, where the helmet-slot pieces stop above it.\nHEADS = [1362163]"+s[b:]
edit(R/"work/v20-char/build_character.py",bc)
def pack(s):return rep(s,"opem-amalur-scene-v0.30-arm64.apk","opem-amalur-scene-v0.31-arm64.apk")
edit(r/"package_android.py",pack)
def man(s):return rep(rep(s,'android:versionCode="32"','android:versionCode="33"'),'android:versionName="0.30.0"','android:versionName="0.31.0"')
edit(r/"AndroidManifest.xml",man)
# Materials of the current pack: only the flags change.
syms=json.loads((R/"work/v20-inputs/symbols.json").read_text());M=json.loads((R/"work/v22-stress/zone-dal/zone_materials.json").read_text())["materials"]
f=R/"work/v22-stress/live-pack/materials.bin";b=bytearray(f.read_bytes());n=struct.unpack_from("<I",b,0)[0];assert n==len(M);hit=0
for i,m in enumerate(M):
    if not m.get("terrain") and "skyline" in str(syms["texture"].get(str(m["d"]),"")):
        o=4+i*28;fl=struct.unpack_from("<I",b,o)[0];struct.pack_into("<I",b,o,fl|4);hit+=1
f.write_bytes(bytes(b));print("skyline materials",hit,"ok")
