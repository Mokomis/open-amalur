import re
from pathlib import Path
R=Path.home()/"Documents/Opem Amalur";r=R/"work/v19-host"
def edit(f,fn):
    s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n");s=fn(s)
    if crlf:s=s.replace("\n","\r\n")
    f.write_bytes(s.encode())
def rep(s,a,b):
    assert a in s,a[:70]
    return s.replace(a,b,1)
def bc(s):
    a=s.index('CLIPS = [(673754, "combat_idle")');b=s.index("\n",a)
    return s[:a]+'''_anim = lambda name: next(int(k) for k, v in syms["animation"].items() if v == name)
# Exploring uses the ordinary clips; 3 to 7 are the fight; 8 to 10 are the same movement in a fighting stance.
CLIPS = [(_anim("human_idle_01"), "idle"), (_anim("human_walk_01"), "walk"), (_anim("human_run_01"), "run"), (673833, "attack_b"), (1893691, "attack_special"), (673835, "attack_x"), (673903, "react_front"), (1926549, "react_death"), (673754, "combat_idle"), (673863, "combat_walk"), (673928, "combat_run")]'''+s[b:]
edit(R/"work/v20-char/build_character.py",bc)
def ch(s):
    s=rep(s,"OA_CHAR_MAX_CLIPS=10,","OA_CHAR_MAX_CLIPS=12,")
    s=rep(s,"enum{OA_CLIP_IDLE=0,OA_CLIP_WALK=1,OA_CLIP_RUN=2};","enum{OA_CLIP_IDLE=0,OA_CLIP_WALK=1,OA_CLIP_RUN=2,OA_CLIP_COMBAT=8};")
    s=rep(s," float time[OA_CHAR_MAX_CLIPS],weight[OA_CHAR_MAX_CLIPS];\n"," float time[OA_CHAR_MAX_CLIPS],weight[OA_CHAR_MAX_CLIPS];\n /* How fast each clip's planted foot travels, measured from the clip; 0 when it has none. */\n float clip_speed[OA_CHAR_MAX_CLIPS];\n /* Moves with the clips from OA_CLIP_COMBAT when the character has them. */\n int combat_stance;\n")
    return s
edit(r/"oa_character.h",ch)
def cc(s):
    s=rep(s,"int oa_character_parse(oa_character *c,",r'''/* Forward speed the clip was animated for: how fast the lowest moving joint travels while it is on the ground. */
static float planted_speed(const oa_character *c,const oa_char_clip *k){
 uint32_t f,j,best=0,frames=k->frames,joints=c->joints;float *w=(float*)malloc(sizeof(float)*3u*frames*joints),(*q)[4]=(float(*)[4])malloc(sizeof(float)*4u*joints),lowest=1e30f,floor_z=1e30f,sum=0;unsigned count=0;
 if(!w||!q){free(w);free(q);return 0;}
 for(f=0;f<frames;f++)for(j=0;j<joints;j++){const float *a=k->pose+(size_t)(f*joints+j)*7;float *p=w+(size_t)(f*joints+j)*3;if(c->parents[j]<0){memcpy(q[j],a,16);memcpy(p,a+4,12);}else{int up=c->parents[j];float r[3];qmul(q[j],q[up],a);qrot(r,q[up],a+4);p[0]=w[(size_t)(f*joints+(uint32_t)up)*3]+r[0];p[1]=w[(size_t)(f*joints+(uint32_t)up)*3+1]+r[1];p[2]=w[(size_t)(f*joints+(uint32_t)up)*3+2]+r[2];}}
 for(j=0;j<joints;j++){float mean=0,x0=1e30f,x1=-1e30f;for(f=0;f<frames;f++){const float *p=w+(size_t)(f*joints+j)*3;mean+=p[2];if(p[0]<x0)x0=p[0];if(p[0]>x1)x1=p[0];}mean/=(float)frames;if(x1-x0>5.f&&mean<lowest){lowest=mean;best=j;}}
 if(lowest<1e29f){for(f=0;f<frames;f++){float z=w[(size_t)(f*joints+best)*3+2];if(z<floor_z)floor_z=z;}
  for(f=0;f+1<frames;f++){const float *p=w+(size_t)(f*joints+best)*3,*n=w+(size_t)((f+1)*joints+best)*3;if(p[2]<=floor_z+6.f){float dx=n[0]-p[0],dy=n[1]-p[1];sum+=sqrtf(dx*dx+dy*dy)*k->fps;count++;}}}
 free(w);free(q);return count?sum/(float)count:0;}
int oa_character_parse(oa_character *c,''')
    s=rep(s," c->bytes=bytes;c->size=size;c->weight[OA_CLIP_IDLE]=1;c->oneshot=-1;c->ready=1;oa_character_pose(c);return 1;"," {static const uint32_t moves[4]={OA_CLIP_WALK,OA_CLIP_RUN,OA_CLIP_COMBAT+OA_CLIP_WALK,OA_CLIP_COMBAT+OA_CLIP_RUN};for(i=0;i<4;i++)if(moves[i]<c->clip_count&&(moves[i]<3||c->clip_count>OA_CLIP_COMBAT+2u))c->clip_speed[moves[i]]=planted_speed(c,c->clips+moves[i]);}\n c->bytes=bytes;c->size=size;c->weight[OA_CLIP_IDLE]=1;c->oneshot=-1;c->ready=1;oa_character_pose(c);return 1;")
    a=s.index(" /* Authored thresholds and playback rates chosen to limit visible foot sliding. */");b=s.index("void oa_character_play(")
    s=s[:a]+r''' /* Playback follows travel speed, so a planted foot stays put. The walk to run threshold is authored. */
 uint32_t i;float target[OA_CHAR_MAX_CLIPS]={0},fade=dt*(c->oneshot>=0?14.0f:8.0f),sum=0;
 uint32_t base=c->combat_stance&&c->clip_count>OA_CLIP_COMBAT+2u?OA_CLIP_COMBAT:0u;
 uint32_t wanted=base+(speed<.05f?OA_CLIP_IDLE:speed<.7f?OA_CLIP_WALK:OA_CLIP_RUN);
 if(!c->ready)return;
 if(c->clip_count<3){const oa_char_clip *k=c->clips;c->time[0]=fmodf(c->time[0]+dt,(float)(k->frames-1)/k->fps);return;}
 target[c->oneshot>=0?(uint32_t)c->oneshot:wanted]=1;if(fade>1)fade=1;
 for(i=0;i<c->clip_count;i++){const oa_char_clip *k=c->clips+i;float period=(float)(k->frames-1)/k->fps;
  c->weight[i]+=(target[i]-c->weight[i])*fade;sum+=c->weight[i];
  if((int)i==c->oneshot){c->time[i]+=dt*c->oneshot_rate;if(c->time[i]>=period){c->time[i]=period;if(!c->oneshot_hold)c->oneshot=-1;}}
  else if(i<3||i>=OA_CLIP_COMBAT){uint32_t role=i>=OA_CLIP_COMBAT?i-OA_CLIP_COMBAT:i;float rate=1.f;if(role){float travel=c->clip_speed[i]>1.f?c->clip_speed[i]:(role==OA_CLIP_WALK?150.f:420.f);rate=velocity_units/travel;if(rate<.5f)rate=.5f;if(rate>2.f)rate=2.f;}c->time[i]=fmodf(c->time[i]+dt*rate,period);}}
 if(sum>0)for(i=0;i<c->clip_count;i++)c->weight[i]/=sum;
}
'''+s[b:]
    return s
edit(r/"oa_character.c",cc)
def test(s):
    s=rep(s,"c.clip_count==8&&","c.clip_count==11&&")
    s=rep(s,"CHECK(c.weight[OA_CLIP_RUN]>.99f);","CHECK(c.weight[OA_CLIP_RUN]>.99f);CHECK(c.clip_speed[OA_CLIP_WALK]>200.f&&c.clip_speed[OA_CLIP_WALK]<400.f);CHECK(c.clip_speed[OA_CLIP_RUN]>350.f&&c.clip_speed[OA_CLIP_RUN]<650.f);c.combat_stance=1;for(k=0;k<120;k++)oa_character_animate(&c,1.f,420.f,1/60.f);CHECK(c.weight[OA_CLIP_COMBAT+OA_CLIP_RUN]>.99f);c.combat_stance=0;for(k=0;k<120;k++)oa_character_animate(&c,1.f,420.f,1/60.f);CHECK(c.weight[OA_CLIP_RUN]>.99f);")
    return s
edit(r/"oa_character_test.c",test)
def scene(s):
    s,c=re.subn(r"(for\(m=0;m<OA_WEAPON_MODELS;m\+\+\)if\(\(int\)m!=oa_bag_weapon_model\(&menu\.bag\)\)c\.character\.hidden\|=1u<<\(base\+m\);)",r"\1/* The sword is drawn only for a fight; there is no sheathed model yet. */if(!c.character.combat_stance)for(m=0;m<OA_WEAPON_MODELS;m++)c.character.hidden|=1u<<(base+m);",s);assert c==1
    s,c=re.subn(r"movement\.attack_requested=0;\n( +)if\(prof\.tour&&active_stream&&playing\)",lambda m:"{static float stance_time;float focus_hp;const char *focus_name;const oa_combat *f=&c.combat;float fx=c.foe.feet[0]-c.body.feet[0],fy=c.foe.feet[1]-c.body.feet[1];\n"+m.group(1)+" if(movement.attack_requested||f->player_clip||f->player_dead||(c.foe_ready&&(f->foe==OA_FOE_CHASE||f->foe==OA_FOE_ATTACK||f->foe==OA_FOE_HIT)&&fx*fx+fy*fy<2200.f*2200.f)||oa_actors_focus(active_actors,c.body.feet,&focus_hp,&focus_name))stance_time=4.f;else if(stance_time>0)stance_time-=dt;c.character.combat_stance=stance_time>0;}\n"+m.group(1)+"movement.attack_requested=0;\n"+m.group(1)+"if(prof.tour&&active_stream&&playing)",s);assert c==1
    s=rep(s,'moving=%u chasing=%u bodies=%u drawn=%u models=%u rays=%u update_ms=%.2f",as.total,as.near_count,as.moving,as.chasing,as.slots,as.drawn,as.models,as.rays,as.update_ms','moving=%u chasing=%u bodies=%u drawn=%u models=%u rays=%u capsules=%u update_ms=%.2f",as.total,as.near_count,as.moving,as.chasing,as.slots,as.drawn,as.models,as.rays,as.capsules,as.update_ms')
    s=rep(s,"oa_character_animate(&c.character,d>=100.f?1.f:0.f,d>=100.f?(float)prof.tour:0.f,dt);","oa_character_animate(&c.character,d>=100.f?1.f:0.f,d>=100.f?(float)prof.tour:0.f,dt);")if False else s
    return s
edit(r/"android_scene.c",scene)
def pack(s):return rep(s,"opem-amalur-scene-v0.29-arm64.apk","opem-amalur-scene-v0.30-arm64.apk")
edit(r/"package_android.py",pack)
def man(s):return rep(rep(s,'android:versionCode="31"','android:versionCode="32"'),'android:versionName="0.29.0"','android:versionName="0.30.0"')
edit(r/"AndroidManifest.xml",man)
print("ok")
