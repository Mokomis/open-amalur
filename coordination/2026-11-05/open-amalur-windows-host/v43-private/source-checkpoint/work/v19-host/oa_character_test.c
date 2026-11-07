/* Loads the packaged character asset and checks body proportions through all clips. */
#include "oa_npc.h"
#include "oa_combat.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){printf("FAILED line %d: %s\n",__LINE__,#x);return 1;}checks++;}while(0)
int main(int argc,char **argv){
 oa_character c;char error[128];FILE *f;long n,n_bytes;uint8_t *b,*bad;int checks=0;uint32_t i,k;
 if(argc!=3)return 2;f=fopen(argv[1],"rb");if(!f)return 2;fseek(f,0,SEEK_END);n=ftell(f);rewind(f);b=(uint8_t*)malloc((size_t)n);if(fread(b,1,(size_t)n,f)!=(size_t)n)return 2;fclose(f);
 /* Every truncation must be refused without reading past the end. */
 for(k=0;k<400;k++){size_t cut=(size_t)((uint64_t)n*k/400);bad=(uint8_t*)malloc(cut+1);memcpy(bad,b,cut);CHECK(!oa_character_parse(&c,bad,cut,error,sizeof(error)));free(bad);}
 CHECK(oa_character_parse(&c,b,(size_t)n,error,sizeof(error)));CHECK(c.joints==64&&c.clip_count==OA_CHAR_MAX_CLIPS&&c.part_count>=5);
 for(i=0;i<3;i++){memset(c.weight,0,sizeof(c.weight));c.weight[i]=1;
  for(k=0;k<c.clips[i].frames-1;k+=3){float head,toe_l,toe_r;c.time[i]=(float)k/c.clips[i].fps;oa_character_pose(&c);
   head=c.world_t[21][2];toe_l=c.world_t[6][2];toe_r=c.world_t[12][2];
   CHECK(head>110&&head<195);CHECK(toe_l>-25&&toe_l<80);CHECK(toe_r>-25&&toe_r<80);}}
 memset(c.time,0,sizeof(c.time));memset(c.weight,0,sizeof(c.weight));c.weight[0]=1;c.feet[0]=100;c.feet[1]=-50;c.feet[2]=7;
 for(k=0;k<300;k++){oa_character_animate(&c,k<100?0.f:k<200?.3f:1.f,k<100?0.f:k<200?120.f:420.f,1/60.f);oa_character_pose(&c);
  {float all=0;uint32_t w;for(w=0;w<c.clip_count;w++)all+=c.weight[w];CHECK(fabsf(all-1)<.001f);}}
 CHECK(c.weight[OA_CLIP_RUN]>.99f);CHECK(c.clip_speed[OA_CLIP_WALK]>200.f&&c.clip_speed[OA_CLIP_WALK]<400.f);CHECK(c.clip_speed[OA_CLIP_RUN]>350.f&&c.clip_speed[OA_CLIP_RUN]<650.f);/* A stop, then a start straight ahead, then a turn back: each plays and hands on to its loop. */for(k=0;k<3;k++)oa_character_animate(&c,0,0,1/60.f);CHECK(c.move_clip==OA_CLIP_RUN_STOP);for(k=0;k<120;k++)oa_character_animate(&c,0,0,1/60.f);CHECK(c.move_clip==-1&&c.weight[OA_CLIP_IDLE]>.99f);c.move_target=c.facing;oa_character_animate(&c,1.f,420.f,1/60.f);CHECK(c.move_clip==OA_CLIP_RUN_START);for(k=0;k<3;k++)oa_character_animate(&c,0,0,1/60.f);CHECK(c.move_clip==OA_CLIP_RUN_STOP_SHORT);for(k=0;k<120;k++)oa_character_animate(&c,0,0,1/60.f);c.move_target=c.facing+3.1f;oa_character_animate(&c,1.f,420.f,1/60.f);CHECK(c.move_clip==OA_CLIP_RUN_TURN_BACK);CHECK(c.turn_total!=0);CHECK(oa_character_turn_step(&c,3.1f,1/60.f)==0);for(k=0;k<20;k++)oa_character_animate(&c,1.f,420.f,1/60.f);CHECK(oa_character_turn_step(&c,3.1f,1/60.f)>0);for(k=0;k<120;k++)oa_character_animate(&c,1.f,420.f,1/60.f);CHECK(c.move_clip==-1&&c.weight[OA_CLIP_RUN]>.99f);CHECK(c.lean_delta!=NULL);c.slope=1;c.lean=-1;oa_character_pose(&c);{float qn=c.world_q[20][0]*c.world_q[20][0]+c.world_q[20][1]*c.world_q[20][1]+c.world_q[20][2]*c.world_q[20][2]+c.world_q[20][3]*c.world_q[20][3];CHECK(qn>.99f&&qn<1.01f);}c.slope=c.lean=0;c.combat_stance=1;for(k=0;k<120;k++)oa_character_animate(&c,1.f,420.f,1/60.f);CHECK(c.weight[OA_CLIP_COMBAT+OA_CLIP_RUN]>.99f);c.combat_stance=0;for(k=0;k<120;k++)oa_character_animate(&c,1.f,420.f,1/60.f);CHECK(c.weight[OA_CLIP_RUN]>.99f);
 {float rows[OA_CHAR_MAX_PALETTE*12];for(i=0;i<c.part_count;i++){uint32_t m=oa_character_bones(&c,c.parts+i,rows),e;CHECK(m==c.parts[i].palette_count);
   for(e=0;e<m;e++){const float *r=rows+e*12;CHECK(fabsf(r[0]*r[0]+r[1]*r[1]+r[2]*r[2]-1)<.01f);CHECK(fabsf(r[3]-100)<220&&fabsf(r[7]+50)<220&&r[11]>-240&&r[11]<400);}}}
 for(i=3;i<c.clip_count;i++){oa_character_play(&c,(int)i,i==OA_FIGHT_DEATH,1);CHECK(c.oneshot==(int)i);for(k=0;k<400;k++){oa_character_animate(&c,0,0,1/60.f);oa_character_pose(&c);}CHECK(i==OA_FIGHT_DEATH?c.oneshot==(int)i:c.oneshot==-1);oa_character_stop(&c);}
 oa_character_free(&c);
 {oa_combat f;float me[3]={0,0,0},foe[3]={1000,0,0};int kills=0,swings=0,frames,hits=0;
  /* Foe approaches, then the player taps until it falls. */
  oa_combat_reset(&f);oa_combat_step(&f,1/60.f,0,me,0,foe);CHECK(f.foe==OA_FOE_CHASE);oa_combat_step(&f,1/60.f,0,me,0,foe);CHECK(f.foe_vx<0);
  foe[0]=150;for(frames=0;frames<3600&&!kills;frames++){int tap=frames%30==0;oa_combat_step(&f,1/60.f,tap,me,0,foe);if(oa_fight_is_swing(f.play_player))swings++;if(f.foe_struck)hits++;if(f.foe==OA_FOE_DEAD)kills=1;}
  CHECK(kills);CHECK(hits>=5);CHECK(swings>=2);CHECK(f.foe_hp==0);
  for(k=0;k<500&&!f.respawn_foe;k++)oa_combat_step(&f,1/60.f,0,me,0,foe);CHECK(f.respawn_foe);CHECK(f.foe_hp==f.foe_max);
  /* A player who never fights back dies and respawns healed. */
  oa_combat_reset(&f);for(frames=0;frames<7200&&!f.player_dead;frames++){oa_combat_step(&f,1/60.f,0,me,0,foe);}CHECK(f.player_dead);CHECK(f.player_hp==0);CHECK(f.player_locked);
  for(k=0;k<400&&!f.respawn_player;k++)oa_combat_step(&f,1/60.f,1,me,0,foe);CHECK(f.respawn_player);CHECK(f.player_hp==f.player_max);
  /* Out of reach or facing away does no damage. */
  oa_combat_reset(&f);foe[0]=900;for(k=0;k<300;k++)oa_combat_step(&f,1/60.f,k%30==0,me,0,foe);CHECK(f.foe_hp==f.foe_max);
  oa_combat_reset(&f);foe[0]=150;f.foe=OA_FOE_DEAD;f.foe_time=-1000;f.foe_hp=50;for(k=0;k<300;k++)oa_combat_step(&f,1/60.f,k%30==0,me,3.14159f,foe);CHECK(f.foe_hp==50);}
 {static oa_npcs n;uint8_t *people;f=fopen(argv[2],"rb");if(!f)return 2;fseek(f,0,SEEK_END);n_bytes=ftell(f);rewind(f);people=(uint8_t*)malloc((size_t)n_bytes);if(fread(people,1,(size_t)n_bytes,f)!=(size_t)n_bytes)return 2;fclose(f);
  for(k=0;k<60;k++){size_t cut=(size_t)((uint64_t)n_bytes*k/60);CHECK(!oa_npcs_parse(&n,people,cut,error,sizeof(error)));}
  CHECK(oa_npcs_parse(&n,people,(size_t)n_bytes,error,sizeof(error)));CHECK(n.count>=8);
  for(k=0;k<120;k++)oa_npcs_update(&n,1/60.f);
  for(i=0;i<n.count;i++){float head=n.people[i].world_t[21][2];CHECK(head>120&&head<200);CHECK(n.people[i].feet[2]>4000&&n.people[i].feet[2]<8000);}
  oa_npcs_free(&n);free(people);}
 printf("character-test: %d checks passed\n",checks);return 0;
}
