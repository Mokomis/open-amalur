from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";h=root/"work/v19-host";wc=root/"work/v20-char"
def sub(p,pairs):
    t=p.read_text(encoding="utf-8")
    for a,b in pairs:
        assert a in t,a
        t=t.replace(a,b)
    p.write_text(t,encoding="utf-8",newline="\n")
sub(wc/"build_character.py",[
 ('"human_sword_attack_xxxx_02"]\n','"human_sword_attack_xxxx_02",\n      # Player motion set: 12 to 21 starts, stops and turns; 22 to 25 slope and lean poses; 26 to 29 idle variations.\n      "human_run_start_01", "human_run_stop_01", "human_run_stop_short_01", "human_M_walk_Start", "human_M_walk_stop", "Human_Idle_turn_90_Left_Ent_Run", "Human_Idle_turn_90_Right_Ent_Run", "Human_Idle_turn_180_Right_Ent_Run", "human_M_Idle_Turn_90_Left_walk", "human_M_Idle_Turn_90_Rgt_walk", "human_run_Slope_Up_Blend", "human_run_Slope_Down_Blend", "human_run_turn_left_Blend", "human_run_turn_Right_Blend", "Player_Idle_Variation01", "Player_Idle_Variation03", "Player_Idle_Variation04", "Player_Idle_Variation05"]\n'),
])
sub(h/"oa_character.h",[
 ('OA_CHAR_MAX_CLIPS=12,','OA_CHAR_MAX_CLIPS=30,'),
 ('enum{OA_CLIP_IDLE=0,OA_CLIP_WALK=1,OA_CLIP_RUN=2,OA_CLIP_COMBAT=8};','enum{OA_CLIP_IDLE=0,OA_CLIP_WALK=1,OA_CLIP_RUN=2,OA_CLIP_COMBAT=8,OA_CLIP_RUN_START=12,OA_CLIP_RUN_STOP=13,OA_CLIP_RUN_STOP_SHORT=14,OA_CLIP_WALK_START=15,OA_CLIP_WALK_STOP=16,OA_CLIP_RUN_TURN_LEFT=17,OA_CLIP_RUN_TURN_RIGHT=18,OA_CLIP_RUN_TURN_BACK=19,OA_CLIP_WALK_TURN_LEFT=20,OA_CLIP_WALK_TURN_RIGHT=21,OA_CLIP_SLOPE_UP=22,OA_CLIP_SLOPE_DOWN=23,OA_CLIP_LEAN_LEFT=24,OA_CLIP_LEAN_RIGHT=25,OA_CLIP_IDLE_VARIATION=26};'),
 (' float oneshot_rate;\n',' float oneshot_rate;\n /* Start, stop, turn or idle variation playing over locomotion; -1 when none. Only characters with every clip have these. */\n int move_clip,was_moving;\n float moved_for,idle_for,idle_next,turn_total,move_target;\n uint32_t idle_seed;\n /* Pose differences from the slope and lean clips, -1..1 each; NULL without those clips. */\n float *lean_delta,slope,lean;\n'),
 ('void oa_character_play(','/* Radians the body may turn this frame toward an angle turn away. */\nfloat oa_character_turn_step(const oa_character *c,float turn,float dt);\nvoid oa_character_play('),
])
sub(h/"oa_character.c",[
 # parse: deltas
 (' c->bytes=bytes;c->size=size;c->weight[OA_CLIP_IDLE]=1;c->oneshot=-1;',''' c->move_clip=-1;c->idle_next=14.f;c->idle_seed=431608u;
 /* The slope and lean clips hold one pose each, relative to a reference this code has not recovered. The difference within each pair is what is used: half of it either way about their middle. */
 if(c->clip_count==OA_CHAR_MAX_CLIPS&&(c->lean_delta=(float*)malloc(sizeof(float)*8u*c->joints))!=NULL){uint32_t j,pair;for(pair=0;pair<2;pair++)for(j=0;j<c->joints;j++){const oa_char_clip *ka=c->clips+OA_CLIP_SLOPE_UP+pair*2,*kb=ka+1;const float *qa=ka->pose+(size_t)(ka->frames/2u*c->joints+j)*7,*qb=kb->pose+(size_t)(kb->frames/2u*c->joints+j)*7;float s=qa[0]*qb[0]+qa[1]*qb[1]+qa[2]*qb[2]+qa[3]*qb[3]<0?-1.f:1.f,m[4],n,*d=c->lean_delta+(size_t)(pair*c->joints+j)*4;uint32_t e;for(e=0;e<4;e++)m[e]=qa[e]+qb[e]*s;n=sqrtf(m[0]*m[0]+m[1]*m[1]+m[2]*m[2]+m[3]*m[3]);if(n<1e-4f){d[0]=d[1]=d[2]=0;d[3]=1;continue;}for(e=0;e<3;e++)m[e]=-m[e]/n;m[3]/=n;qmul(d,qa,m);}}
 c->bytes=bytes;c->size=size;c->weight[OA_CLIP_IDLE]=1;c->oneshot=-1;'''),
 ('void oa_character_free(oa_character *c){free(c->bytes);','void oa_character_free(oa_character *c){free(c->lean_delta);free(c->bytes);'),
 # animate
 ('void oa_character_animate(oa_character *c,float speed,float velocity_units,float dt){',r'''/* The loop frame closest to where a clip ends, so it leads into the loop without a step. */
static float loop_entry(const oa_character *c,const oa_char_clip *from,const oa_char_clip *loop){
 uint32_t f,j,best=0;float low=1e30f;const float *end=from->pose+(size_t)(from->frames-1u)*c->joints*7;
 for(f=0;f+1<loop->frames;f++){float e=0;const float *p=loop->pose+(size_t)f*c->joints*7;for(j=0;j<c->joints;j++){const float *a=end+j*7,*b=p+j*7;float d=a[0]*b[0]+a[1]*b[1]+a[2]*b[2]+a[3]*b[3];e+=1.f-d*d;}if(e<low){low=e;best=f;}}
 return (float)best/loop->fps;}
/* Which clip carries a change of movement. The 45 and 135 degree limits and the 0.5 second short stop are authored. */
static void movement_change(oa_character *c,int moving,int running,float dt){
 if(c->oneshot>=0){c->move_clip=-1;c->was_moving=moving;c->idle_for=0;return;}
 if(moving&&!c->was_moving){float turn=remainderf(c->move_target-c->facing,6.283185307f),size=fabsf(turn);int clip;
  c->turn_total=0;
  if(size<.7854f)clip=running?OA_CLIP_RUN_START:OA_CLIP_WALK_START;
  else{c->turn_total=turn;if(size>2.3562f&&running)clip=OA_CLIP_RUN_TURN_BACK;else if(running)clip=turn>0?OA_CLIP_RUN_TURN_LEFT:OA_CLIP_RUN_TURN_RIGHT;else clip=turn>0?OA_CLIP_WALK_TURN_LEFT:OA_CLIP_WALK_TURN_RIGHT;}
  c->move_clip=clip;c->time[clip]=0;c->moved_for=0;}
 else if(!moving&&c->was_moving){int clip=c->weight[OA_CLIP_RUN]+c->weight[OA_CLIP_COMBAT+OA_CLIP_RUN]+(c->move_clip==OA_CLIP_RUN_START||c->move_clip==OA_CLIP_RUN_TURN_LEFT||c->move_clip==OA_CLIP_RUN_TURN_RIGHT||c->move_clip==OA_CLIP_RUN_TURN_BACK?1.f:0.f)>.5f?(c->moved_for<.5f?OA_CLIP_RUN_STOP_SHORT:OA_CLIP_RUN_STOP):OA_CLIP_WALK_STOP;c->move_clip=clip;c->time[clip]=0;c->turn_total=0;c->idle_for=0;}
 if(moving){c->moved_for+=dt;c->idle_for=0;}
 else if(c->move_clip<0&&!c->combat_stance){c->idle_for+=dt;if(c->idle_for>c->idle_next){int clip=OA_CLIP_IDLE_VARIATION+(int)((c->idle_seed>>16)%4u);c->idle_seed=c->idle_seed*1103515245u+12345u;c->move_clip=clip;c->time[clip]=0;c->idle_for=0;c->idle_next=14.f+(float)((c->idle_seed>>16)%12u);}}
 c->was_moving=moving;}
float oa_character_turn_step(const oa_character *c,float turn,float dt){
 /* A turn clip leads with the upper body and carries no net rotation, so the body follows after its first fifth. The rate is authored to fit the clip. */
 float step=dt*12.0f;
 if(c->turn_total!=0&&c->move_clip>=0&&c->lean_delta){const oa_char_clip *k=c->clips+c->move_clip;float period=(float)(k->frames-1)/k->fps;if(c->time[c->move_clip]<period*.2f)return 0;step=fabsf(c->turn_total)/(period*.4f)*dt;}
 return turn>step?step:turn<-step?-step:turn;}
void oa_character_animate(oa_character *c,float speed,float velocity_units,float dt){'''),
 ('float target[OA_CHAR_MAX_CLIPS]={0},fade=dt*(c->oneshot>=0?14.0f:8.0f),sum=0;','float target[OA_CHAR_MAX_CLIPS]={0},fade=dt*(c->oneshot>=0||c->move_clip>=0?14.0f:8.0f),sum=0;'),
 (' target[c->oneshot>=0?(uint32_t)c->oneshot:wanted]=1;if(fade>1)fade=1;',' if(c->lean_delta)movement_change(c,speed>=.05f,speed>=.7f,dt);\n target[c->oneshot>=0?(uint32_t)c->oneshot:c->move_clip>=0?(uint32_t)c->move_clip:wanted]=1;if(fade>1)fade=1;'),
 ("if(!c->oneshot_hold)c->oneshot=-1;}}\n  else if(i<3||i>=OA_CLIP_COMBAT){","if(!c->oneshot_hold)c->oneshot=-1;}}\n  else if((int)i==c->move_clip){c->time[i]+=dt;if(c->time[i]>=period){c->time[i]=period;c->move_clip=-1;c->turn_total=0;if(speed>=.05f){uint32_t role=speed<.7f?OA_CLIP_WALK:OA_CLIP_RUN;c->time[role]=loop_entry(c,k,c->clips+role);if(c->clip_count>OA_CLIP_COMBAT+role)c->time[OA_CLIP_COMBAT+role]=c->time[role];}}}\n  else if(i<3||(i>=OA_CLIP_COMBAT&&i<OA_CLIP_COMBAT+3u)){"),
 # pose overlay
 ("  n=sqrtf(q[0]*q[0]+q[1]*q[1]+q[2]*q[2]+q[3]*q[3]);if(n>0){q[0]/=n;q[1]/=n;q[2]/=n;q[3]/=n;}else q[3]=1;\n","  n=sqrtf(q[0]*q[0]+q[1]*q[1]+q[2]*q[2]+q[3]*q[3]);if(n>0){q[0]/=n;q[1]/=n;q[2]/=n;q[3]/=n;}else q[3]=1;\n  if(c->lean_delta&&(c->slope!=0||c->lean!=0)){uint32_t pair;for(pair=0;pair<2;pair++){float amount=pair?c->lean:c->slope,dq[4];const float *d=c->lean_delta+(size_t)(pair*c->joints+j)*4;uint32_t e;if(amount==0||(d[0]==0&&d[1]==0&&d[2]==0))continue;dq[0]=d[0]*amount;dq[1]=d[1]*amount;dq[2]=d[2]*amount;dq[3]=1.f+(d[3]-1.f)*fabsf(amount);n=sqrtf(dq[0]*dq[0]+dq[1]*dq[1]+dq[2]*dq[2]+dq[3]*dq[3]);for(e=0;e<4;e++)dq[e]/=n;qmul(q,dq,q);}}\n"),
])
sub(h/"android_scene.c",[
 ("target=atan2f(vy,vx),turn=remainderf(target-c->character.facing,6.283185307f),step=dt*12.0f;\n        c->character.facing=remainderf(c->character.facing+(turn>step?step:turn<-step?-step:turn),6.283185307f);}\n    memcpy(c->character.feet,c->body.feet,sizeof(c->body.feet));\n",
  "target=atan2f(vy,vx),turn=remainderf(target-c->character.facing,6.283185307f),before=c->character.facing;\n        c->character.move_target=target;c->character.facing=remainderf(c->character.facing+oa_character_turn_step(&c->character,turn,dt),6.283185307f);lean_rate=remainderf(c->character.facing-before,6.283185307f)/(dt>.0001f?dt:.0001f);}\n    /* How hard the slope and lean poses apply. The full-strength slope of 0.6 and turn of 6 radians a second are authored; both fade in over a fifth of a second. */\n    {float dx=c->body.feet[0]-c->character.feet[0],dy=c->body.feet[1]-c->character.feet[1],run=sqrtf(dx*dx+dy*dy),want_slope=run>.5f&&speed>=.7f?clampf((c->body.feet[2]-c->character.feet[2])/run/.6f,-1.f,1.f):0.f,want_lean=speed>=.7f?clampf(lean_rate/6.f,-1.f,1.f):0.f,ease=dt*5.f>1.f?1.f:dt*5.f;c->character.slope+=(want_slope-c->character.slope)*ease;c->character.lean+=(want_lean-c->character.lean)*ease;if(fabsf(c->character.slope)<.01f)c->character.slope=0;if(fabsf(c->character.lean)<.01f)c->character.lean=0;}\n    memcpy(c->character.feet,c->body.feet,sizeof(c->body.feet));\n"),
 ("float speed=sqrtf(right*right+forward*forward),pivot[3],back[3],hit=0,want=OA_CAMERA_BOOM;","float speed=sqrtf(right*right+forward*forward),pivot[3],back[3],hit=0,want=OA_CAMERA_BOOM,lean_rate=0;"),
])
sub(h/"oa_character_test.c",[("c.clip_count==12&&","c.clip_count==OA_CHAR_MAX_CLIPS&&"),
 ("c.combat_stance=1;for(k=0;k<120;k++)oa_character_animate(&c,1.f,420.f,1/60.f);CHECK(c.weight[OA_CLIP_COMBAT+OA_CLIP_RUN]>.99f);",
  "/* A stop, then a start straight ahead, then a turn back: each plays and hands on to its loop. */for(k=0;k<3;k++)oa_character_animate(&c,0,0,1/60.f);CHECK(c.move_clip==OA_CLIP_RUN_STOP);for(k=0;k<120;k++)oa_character_animate(&c,0,0,1/60.f);CHECK(c.move_clip==-1&&c.weight[OA_CLIP_IDLE]>.99f);c.move_target=c.facing;oa_character_animate(&c,1.f,420.f,1/60.f);CHECK(c.move_clip==OA_CLIP_RUN_START);for(k=0;k<3;k++)oa_character_animate(&c,0,0,1/60.f);CHECK(c.move_clip==OA_CLIP_RUN_STOP_SHORT);for(k=0;k<120;k++)oa_character_animate(&c,0,0,1/60.f);c.move_target=c.facing+3.1f;oa_character_animate(&c,1.f,420.f,1/60.f);CHECK(c.move_clip==OA_CLIP_RUN_TURN_BACK);CHECK(c.turn_total!=0);CHECK(oa_character_turn_step(&c,3.1f,1/60.f)==0);for(k=0;k<20;k++)oa_character_animate(&c,1.f,420.f,1/60.f);CHECK(oa_character_turn_step(&c,3.1f,1/60.f)>0);for(k=0;k<120;k++)oa_character_animate(&c,1.f,420.f,1/60.f);CHECK(c.move_clip==-1&&c.weight[OA_CLIP_RUN]>.99f);CHECK(c.lean_delta!=NULL);c.slope=1;c.lean=-1;oa_character_pose(&c);{float qn=c.world_q[20][0]*c.world_q[20][0]+c.world_q[20][1]*c.world_q[20][1]+c.world_q[20][2]*c.world_q[20][2]+c.world_q[20][3]*c.world_q[20][3];CHECK(qn>.99f&&qn<1.01f);}c.slope=c.lean=0;c.combat_stance=1;for(k=0;k<120;k++)oa_character_animate(&c,1.f,420.f,1/60.f);CHECK(c.weight[OA_CLIP_COMBAT+OA_CLIP_RUN]>.99f);"),
])
print("ok")
