"""Version 0.22.0: sword, attack button, health bars, one enemy."""
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
host = root / "work/v19-host"


def edit(name, pairs):
    f = host / name
    t = f.read_bytes().decode("utf-8")
    for old, new in pairs:
        if t.count(old) != 1:
            raise SystemExit("%s: expected one match for %r, found %d" % (name, old[:90], t.count(old)))
        t = t.replace(old, new)
    f.write_bytes(t.encode("utf-8"))


edit("oa_character.h", [
 ("OA_CHAR_MAX_CLIPS=4,", "OA_CHAR_MAX_CLIPS=10,"),
 (" float facing,feet[3];\n", " float facing,feet[3];\n /* One-shot clip layered over locomotion; -1 when none plays. */\n int oneshot,oneshot_hold;\n float oneshot_rate;\n"),
 ("void oa_character_pose(oa_character *c);", "void oa_character_play(oa_character *c,int clip,int hold,float rate);\nvoid oa_character_stop(oa_character *c);\nvoid oa_character_pose(oa_character *c);"),
])
edit("oa_character.c", [
 ("c->bytes=bytes;c->size=size;c->weight[OA_CLIP_IDLE]=1;c->ready=1;", "c->bytes=bytes;c->size=size;c->weight[OA_CLIP_IDLE]=1;c->oneshot=-1;c->ready=1;"),
 ("""uint32_t i;float rate[3]={1.0f,velocity_units/150.0f,velocity_units/420.0f},target[3]={0,0,0},fade=dt*8.0f,sum=0;""", """uint32_t i;float rate[3]={1.0f,velocity_units/150.0f,velocity_units/420.0f},target[OA_CHAR_MAX_CLIPS]={0},fade=dt*(c->oneshot>=0?14.0f:8.0f),sum=0;"""),
 ("""target[wanted]=1;if(fade>1)fade=1;
 for(i=0;i<3;i++){const oa_char_clip *k=c->clips+i;float period=(float)(k->frames-1)/k->fps;
  c->weight[i]+=(target[i]-c->weight[i])*fade;sum+=c->weight[i];
  c->time[i]=fmodf(c->time[i]+dt*rate[i],period);}
 if(sum>0)for(i=0;i<3;i++)c->weight[i]/=sum;""", """target[c->oneshot>=0?c->oneshot:wanted]=1;if(fade>1)fade=1;
 for(i=0;i<c->clip_count;i++){const oa_char_clip *k=c->clips+i;float period=(float)(k->frames-1)/k->fps;
  c->weight[i]+=(target[i]-c->weight[i])*fade;sum+=c->weight[i];
  if(i<3)c->time[i]=fmodf(c->time[i]+dt*rate[i],period);
  else if((int)i==c->oneshot){c->time[i]+=dt*c->oneshot_rate;if(c->time[i]>=period){c->time[i]=period;if(!c->oneshot_hold)c->oneshot=-1;}}}
 if(sum>0)for(i=0;i<c->clip_count;i++)c->weight[i]/=sum;"""),
 ("void oa_character_pose(oa_character *c){", """void oa_character_play(oa_character *c,int clip,int hold,float rate){if(!c->ready||clip<0||(uint32_t)clip>=c->clip_count)return;c->oneshot=clip;c->oneshot_hold=hold;c->oneshot_rate=rate;c->time[clip]=0;}
void oa_character_stop(oa_character *c){c->oneshot=-1;}
void oa_character_pose(oa_character *c){"""),
])
edit("oa_character_test.c", [
 ('#include "oa_npc.h"\n', '#include "oa_npc.h"\n#include "oa_combat.h"\n'),
 ("CHECK(c.joints==64&&c.clip_count==3&&c.part_count>=4);", "CHECK(c.joints==64&&c.clip_count==8&&c.part_count>=5);"),
 ("CHECK(head>130&&head<195);", "CHECK(head>110&&head<195);"),
 ("oa_character_free(&c);\n", """for(i=3;i<c.clip_count;i++){oa_character_play(&c,(int)i,i==OA_FIGHT_DEATH,1);CHECK(c.oneshot==(int)i);for(k=0;k<400;k++){oa_character_animate(&c,0,0,1/60.f);oa_character_pose(&c);}CHECK(i==OA_FIGHT_DEATH?c.oneshot==(int)i:c.oneshot==-1);oa_character_stop(&c);}
 oa_character_free(&c);
 {oa_combat f;float me[3]={0,0,0},foe[3]={1000,0,0};int kills=0,swings=0,frames,hits=0;
  /* Foe approaches, then the player taps until it falls. */
  oa_combat_reset(&f);oa_combat_step(&f,1/60.f,0,me,0,foe);CHECK(f.foe==OA_FOE_CHASE);CHECK(f.foe_vx<0);
  foe[0]=150;for(frames=0;frames<3600&&!kills;frames++){int tap=frames%30==0;oa_combat_step(&f,1/60.f,tap,me,0,foe);if(f.play_player>=OA_FIGHT_ATTACK_A&&f.play_player<=OA_FIGHT_ATTACK_C)swings++;if(f.foe_struck)hits++;if(f.foe==OA_FOE_DEAD)kills=1;}
  CHECK(kills);CHECK(hits>=5);CHECK(swings>=2);CHECK(f.foe_hp==0);
  for(k=0;k<500&&!f.respawn_foe;k++)oa_combat_step(&f,1/60.f,0,me,0,foe);CHECK(f.respawn_foe);CHECK(f.foe_hp==f.foe_max);
  /* A player who never fights back dies and respawns healed. */
  oa_combat_reset(&f);for(frames=0;frames<7200&&!f.player_dead;frames++){oa_combat_step(&f,1/60.f,0,me,0,foe);}CHECK(f.player_dead);CHECK(f.player_hp==0);CHECK(f.player_locked);
  for(k=0;k<400&&!f.respawn_player;k++)oa_combat_step(&f,1/60.f,1,me,0,foe);CHECK(f.respawn_player);CHECK(f.player_hp==f.player_max);
  /* Out of reach or facing away does no damage. */
  oa_combat_reset(&f);foe[0]=900;for(k=0;k<300;k++)oa_combat_step(&f,1/60.f,k%30==0,me,0,foe);CHECK(f.foe_hp==f.foe_max);
  oa_combat_reset(&f);foe[0]=150;f.foe=OA_FOE_DEAD;f.foe_time=-1000;f.foe_hp=50;for(k=0;k<300;k++)oa_combat_step(&f,1/60.f,k%30==0,me,3.14159f,foe);CHECK(f.foe_hp==50);}
"""),
])
edit("exploration_input.h", [("int interact_requested,lighting_requested;", "int interact_requested,lighting_requested,attack_requested;")])
edit("exploration_input.c", [
 ("        if(y>h-112*scale&&y<h-60*scale&&fabsf(x-w*.5f)<160*scale){s->interact_requested=1;return 1;}\n", "        if(y>h-112*scale&&y<h-60*scale&&fabsf(x-w*.5f)<160*scale){s->interact_requested=1;return 1;}\n        if(y>h-210*scale&&y<h-110*scale&&x>w-190*scale){s->attack_requested=1;return 1;}\n"),
 ("case AKEYCODE_E:case AKEYCODE_BUTTON_A:if(action==AKEY_EVENT_ACTION_DOWN&&!AKeyEvent_getRepeatCount(e))s->interact_requested=1;return 1;", "case AKEYCODE_E:case AKEYCODE_BUTTON_A:if(action==AKEY_EVENT_ACTION_DOWN&&!AKeyEvent_getRepeatCount(e))s->interact_requested=1;return 1;\n        case AKEYCODE_F:case AKEYCODE_BUTTON_X:if(action==AKEY_EVENT_ACTION_DOWN&&!AKeyEvent_getRepeatCount(e))s->attack_requested=1;return 1;"),
])
edit("exploration_overlay.h", [
 ("const oa_interaction *interaction,int room_lighting,const char *door_prompt);", "const oa_interaction *interaction,int room_lighting,const char *door_prompt,const float *health);"),
])
edit("exploration_overlay.c", [
 ("const oa_interaction *interaction,int room_lighting,const char *door_prompt){", "const oa_interaction *interaction,int room_lighting,const char *door_prompt,const float *health){"),
 ('''else if(door_prompt){rect(o,w*.5f-160*s,h-112*s,320*s,52*s,dark);text(o,w*.5f-148*s,h-94*s,2*s,door_prompt,white);}
''', '''else if(door_prompt){rect(o,w*.5f-160*s,h-112*s,320*s,52*s,dark);text(o,w*.5f-148*s,h-94*s,2*s,door_prompt,white);}
 /* health: player fraction, enemy fraction or negative to hide, message flag. */
 if(health){const float red[4]={.78f,.13f,.13f,.95f},orange[4]={.85f,.45f,.1f,.95f};
  rect(o,w*.5f-180*s,14*s,360*s,20*s,dark);rect(o,w*.5f-176*s,18*s,352*s*health[0],12*s,red);
  if(health[1]>=0){rect(o,w*.5f-140*s,40*s,280*s,16*s,dark);rect(o,w*.5f-136*s,43*s,272*s*health[1],10*s,orange);}
  rect(o,w-180*s,h-205*s,168*s,90*s,dark);text(o,w-162*s,h-170*s,2*s,"ATTACK",white);
  if(health[2]>0){rect(o,w*.5f-140*s,h*.4f,280*s,52*s,dark);text(o,w*.5f-124*s,h*.4f+18*s,2*s,"YOU HAVE FALLEN",white);}}
'''),
])
edit("android_scene.cmake", [("oa_character.c oa_npc.c oa_character_gl.c ", "oa_character.c oa_npc.c oa_combat.c oa_character_gl.c ")])
edit("CMakeLists.txt", [
 ("VERSION 0.21.0", "VERSION 0.22.0"),
 ("add_executable(oa-character-test oa_character_test.c oa_character.c oa_npc.c)", "add_executable(oa-character-test oa_character_test.c oa_character.c oa_npc.c oa_combat.c)"),
])
edit("android_scene.c", [
 ('#include "oa_npc.h"\n', '#include "oa_npc.h"\n#include "oa_combat.h"\n'),
 ("    oa_character_gpu people[OA_NPC_MAX];\n} graphics;", "    oa_character_gpu people[OA_NPC_MAX];\n    oa_character_gpu foe;\n} graphics;"),
 ("    oa_npcs npcs;\n", "    oa_npcs npcs;\n    /* Fight state. Exists only outdoors. */\n    oa_character foe;\n    opem_controller foe_body;\n    oa_combat combat;\n    int foe_ready;\n    float move_scale;\n"),
 ("oa_character_gpu_close(&g->character);opem_room_lighting_close", "if(g->foe.program)oa_character_gpu_close(&g->foe);oa_character_gpu_close(&g->character);opem_room_lighting_close"),
 ("const oa_npcs *npcs,int outdoor){", "const oa_npcs *npcs,const oa_character *foe,int outdoor){"),
 ('''    {unsigned p;for(p=0;p<npcs->count;p++)if(!oa_character_gpu_open''', '''    if(foe->ready&&!oa_character_gpu_open(&g->foe,foe,outdoor))LOGE("Enemy unavailable");
    {unsigned p;for(p=0;p<npcs->count;p++)if(!oa_character_gpu_open'''),
 ("{unsigned p;for(p=0;p<c->npcs.count;p++)oa_character_gpu_draw(&g->people[p],c->npcs.people+p,matrix,room_lighting,.5f);}}", "if(c->foe_ready)oa_character_gpu_draw(&g->foe,&c->foe,matrix,room_lighting,.5f);\n        {unsigned p;for(p=0;p<c->npcs.count;p++)oa_character_gpu_draw(&g->people[p],c->npcs.people+p,matrix,room_lighting,.5f);}}"),
 ("interaction,room_lighting,door_prompt);\n", "interaction,room_lighting,door_prompt,c->foe_ready?hud:NULL);\n"),
 ("const oa_interaction *interaction,int room_lighting,const char *door_prompt){\n    EGLint width,height;", "const oa_interaction *interaction,int room_lighting,const char *door_prompt){\n    float hud[3];EGLint width,height;\n    {const oa_combat *f=&c->combat;float dx=c->foe.feet[0]-c->body.feet[0],dy=c->foe.feet[1]-c->body.feet[1];hud[0]=f->player_hp/f->player_max;hud[1]=f->foe!=OA_FOE_DEAD&&dx*dx+dy*dy<2200.f*2200.f?f->foe_hp/f->foe_max:-1.f;hud[2]=f->player_dead?1.f:0.f;}"),
 ("(cosf(c->walk_yaw)*forward+sinf(c->walk_yaw)*right)*c->body_config.max_speed,", "(cosf(c->walk_yaw)*forward+sinf(c->walk_yaw)*right)*c->body_config.max_speed*c->move_scale,"),
 ("(sinf(c->walk_yaw)*forward-cosf(c->walk_yaw)*right)*c->body_config.max_speed,dt,", "(sinf(c->walk_yaw)*forward-cosf(c->walk_yaw)*right)*c->body_config.max_speed*c->move_scale,dt,"),
 ("if(c->collision_ready)character_update(c,right,forward,dt);", "if(c->collision_ready)character_update(c,right*c->move_scale,forward*c->move_scale,dt);"),
 ("    oa_npcs_free(&c->npcs);\n    if(world){", '''    oa_npcs_free(&c->npcs);
    if(c->foe.bytes)oa_character_free(&c->foe);
    c->foe_ready=0;c->move_scale=1;oa_combat_reset(&c->combat);oa_character_stop(&c->character);
    if(world&&c->world){AAsset *asset=AAssetManager_open(manager,"town_enemy.bin",AASSET_MODE_BUFFER);
        if(asset){size_t size=(size_t)AAsset_getLength64(asset);uint8_t *bytes=(uint8_t*)malloc(size);const float place[3]={2600.f,-63500.f,5170.f};
            if(bytes&&AAsset_read(asset,bytes,size)==(int)size&&oa_character_parse(&c->foe,bytes,size,error,sizeof(error))){
                if(opem_controller_spawn(c->world,&c->body_config,place,&c->foe_body,error,sizeof(error))){memcpy(c->foe.feet,c->foe_body.feet,sizeof(c->foe.feet));oa_character_pose(&c->foe);c->foe_ready=1;LOGI("Enemy ready at (%.0f %.0f %.0f)",c->foe.feet[0],c->foe.feet[1],c->foe.feet[2]);}
                else LOGE("Enemy spawn rejected: %s",error);}
            else{LOGE("Enemy rejected: %s",bytes?error:"allocation");free(bytes);}
            AAsset_close(asset);}}
    if(world){'''),
 ("graphics_open(&g,s->active_window,&mesh,&materials,&c.character,&c.npcs,world);pthread_mutex_unlock(&s->mutex);", "graphics_open(&g,s->active_window,&mesh,&materials,&c.character,&c.npcs,&c.foe,world);pthread_mutex_unlock(&s->mutex);"),
 ("graphics_open(&g,s->active_window,&mesh,&materials,&c.character,&c.npcs,world);}", "graphics_open(&g,s->active_window,&mesh,&materials,&c.character,&c.npcs,&c.foe,world);}"),
 ("                oa_npcs_update(&c.npcs,dt);\n", '''                oa_npcs_update(&c.npcs,dt);
                if(c.foe_ready&&c.collision_ready&&!interaction.window_open){oa_combat *f=&c.combat;char fight_error[256];
                    oa_combat_step(f,dt,movement.attack_requested&&focused,c.body.feet,c.character.facing,c.foe.feet);
                    if(f->player_turn)c.character.facing=f->player_facing;
                    if(f->play_player>=0)oa_character_play(&c.character,f->play_player,f->hold_player,f->play_player_rate);
                    if(f->play_foe>=0)oa_character_play(&c.foe,f->play_foe,f->hold_foe,1);
                    if(f->respawn_player){oa_character_stop(&c.character);c.spawn_hint=oa_doors[1];exploration_reset(&c);c.character.facing=c.walk_yaw;}
                    if(f->respawn_foe){const float place[3]={2600.f,-63500.f,5170.f};oa_character_stop(&c.foe);if(opem_controller_spawn(c.world,&c.body_config,place,&c.foe_body,fight_error,sizeof(fight_error)))memcpy(c.foe.feet,c.foe_body.feet,sizeof(c.foe.feet));}
                    if(f->foe==OA_FOE_CHASE&&(f->foe_vx!=0||f->foe_vy!=0)){if(opem_controller_step(c.world,&c.body_config,&c.foe_body,f->foe_vx,f->foe_vy,dt,fight_error,sizeof(fight_error)))memcpy(c.foe.feet,c.foe_body.feet,sizeof(c.foe.feet));}
                    else if(f->foe!=OA_FOE_DEAD&&opem_controller_step(c.world,&c.body_config,&c.foe_body,0,0,dt,fight_error,sizeof(fight_error)))memcpy(c.foe.feet,c.foe_body.feet,sizeof(c.foe.feet));
                    c.foe.facing=f->foe_facing;c.move_scale=f->player_locked?0.f:1.f;
                    {float vx=f->foe_vx,vy=f->foe_vy;float speed=sqrtf(vx*vx+vy*vy);oa_character_animate(&c.foe,speed>1?1.f:0.f,speed,dt);oa_character_pose(&c.foe);}}
                movement.attack_requested=0;
'''),
 ("    oa_npcs_free(&c.npcs);\n    oa_character_free(&c.character);\n", "    oa_npcs_free(&c.npcs);\n    if(c.foe.bytes)oa_character_free(&c.foe);\n    oa_character_free(&c.character);\n"),
 ("    exploration_input_clear(&movement);opem_controller_config_default(&c.body_config);\n", "    exploration_input_clear(&movement);opem_controller_config_default(&c.body_config);c.move_scale=1;oa_combat_reset(&c.combat);\n"),
])
edit("AndroidManifest.xml", [('android:versionCode="22" android:versionName="0.21.0"', 'android:versionCode="23" android:versionName="0.22.0"')])
edit("package_android.py", [
 ("opem-amalur-scene-v0.21-arm64.apk", "opem-amalur-scene-v0.22-arm64.apk"),
 ("'town_collision.bin','town_npcs.bin')", "'town_collision.bin','town_npcs.bin','town_enemy.bin')"),
])
print("patched")
