import re
from pathlib import Path
R=Path.home()/"Documents/Opem Amalur";r=R/"work/v19-host"
def edit(f,fn):
    s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n");s=fn(s)
    if crlf:s=s.replace("\n","\r\n")
    f.write_bytes(s.encode())
def rep(s,a,b):
    assert a in s,a[:80]
    return s.replace(a,b,1)
def bc(s):
    a=s.index('CLIPS = [(_anim("human_idle_01"), "idle")');b=s.index("\n",a)
    s=s[:a]+'''_c = ["human_idle_01", "human_walk_01", "human_run_01", "human_sword_attack_x_01", "human_sword_attack_xx_01", "human_sword_attack_xxx_01", "human_norreacfrt", "human_Death_01", "human_sword_idle_01", "human_walk_01", "human_run_01", "human_sword_attack_xxxx_01", "human_sword_attack_x_02", "human_sword_attack_xx_02", "human_sword_attack_xxx_02", "human_sword_attack_xxxx_02"]
CLIPS = [(_anim(n), n) for n in _c]'''+s[b:]
    s=rep(s,"# From the Player motion set. 0 to 2 explore; 3 to 7 are the fight, still the NPC family; 8 to 10 carry the sword, which only changes the idle.","# From the Player, Player_Weapon_Sword and Player_Reactions motion sets. 0 to 2 explore; 3 to 5 and 11 are the combo swings; 6 reacts, 7 dies; 8 to 10 carry the sword, which only changes the idle; 12 to 15 recover from each swing.")
    return s
edit(R/"work/v20-char/build_character.py",bc)
def ch(s):return rep(s,"OA_CHAR_MAX_CLIPS=12,","OA_CHAR_MAX_CLIPS=16,")
edit(r/"oa_character.h",ch)
def ch2(s):
    s=rep(s,"enum{OA_FIGHT_IDLE=0,OA_FIGHT_ATTACK_A=3,OA_FIGHT_ATTACK_B=4,OA_FIGHT_ATTACK_C=5,OA_FIGHT_HIT=6,OA_FIGHT_DEATH=7};","enum{OA_FIGHT_IDLE=0,OA_FIGHT_ATTACK_A=3,OA_FIGHT_ATTACK_B=4,OA_FIGHT_ATTACK_C=5,OA_FIGHT_HIT=6,OA_FIGHT_DEATH=7,OA_FIGHT_ATTACK_D=11,OA_FIGHT_RECOVER=12};\n/* The game's combo: each swing either runs into the next or into its own recovery. */\nstatic inline int oa_fight_is_swing(int clip){return (clip>=OA_FIGHT_ATTACK_A&&clip<=OA_FIGHT_ATTACK_C)||clip==OA_FIGHT_ATTACK_D;}")
    s=rep(s," int player_clip,player_dead,queued;\n"," int player_clip,player_dead,queued,player_stage;\n")
    return s
edit(r/"oa_combat.h",ch2)
def cc(s):
    s=rep(s,"#define PLAYER_RATE 1.25f\n","#define PLAYER_RATE 1.f\n#define FOE_STRIKE 1.1333f\n")
    s=rep(s,"if(c->player_clip!=OA_FIGHT_HIT&&crossed(c->player_clip,before*PLAYER_RATE,c->player_time*PLAYER_RATE)){","if(oa_fight_is_swing(c->player_clip)&&crossed(c->player_clip,before*PLAYER_RATE,c->player_time*PLAYER_RATE)){")
    s=rep(s,"   if(c->queued)c->queued=0;else{float end=c->player_time+SWING_TAIL;if(end<c->player_length)c->player_length=end;}\n","")
    s=rep(s,"  if(attack&&c->player_clip!=OA_FIGHT_HIT)c->queued=1;\n","  if(attack&&oa_fight_is_swing(c->player_clip))c->queued=1;\n  else if(attack&&c->player_clip>=OA_FIGHT_RECOVER)c->player_time=c->player_length,c->queued=2;\n")
    s=rep(s,"  if(c->player_time>=c->player_length){c->queued=0;c->player_clip=0;c->stop_player=1;}}\n","""  if(c->player_time>=c->player_length){
   static const int next[4]={OA_FIGHT_ATTACK_A,OA_FIGHT_ATTACK_B,OA_FIGHT_ATTACK_C,OA_FIGHT_ATTACK_D};
   if(oa_fight_is_swing(c->player_clip)&&c->queued&&c->player_stage<3){c->player_stage++;start_swing(c,next[c->player_stage]);}
   else if(oa_fight_is_swing(c->player_clip)){start_swing(c,OA_FIGHT_RECOVER+c->player_stage);}
   else if(c->queued==2){c->player_stage=0;start_swing(c,OA_FIGHT_ATTACK_A);}
   else{c->queued=0;c->player_clip=0;c->player_stage=0;c->stop_player=1;}}}
""")
    s=rep(s," else if(attack)start_swing(c,OA_FIGHT_ATTACK_C);\n"," else if(attack){c->player_stage=0;start_swing(c,OA_FIGHT_ATTACK_A);}\n")
    s=rep(s,"if(c->play_player>=OA_FIGHT_ATTACK_A&&c->play_player<=OA_FIGHT_ATTACK_C&&c->foe!=OA_FOE_DEAD","if(oa_fight_is_swing(c->play_player)&&c->foe!=OA_FOE_DEAD")
    s=rep(s,"c->foe_length=oa_combat_strikes[OA_FIGHT_ATTACK_C][0]+FOE_SWING_TAIL;","c->foe_length=FOE_STRIKE+FOE_SWING_TAIL;")
    s=rep(s,"if(crossed(OA_FIGHT_ATTACK_C,before,c->foe_time)&&!c->player_dead&&dist<FOE_REACH){","if(before<FOE_STRIKE&&c->foe_time>=FOE_STRIKE&&!c->player_dead&&dist<FOE_REACH){")
    s=rep(s,"c->foe_length=oa_combat_clip_seconds(OA_FIGHT_HIT);c->play_foe=OA_FIGHT_HIT;}}}","c->foe_length=1.3667f;c->play_foe=OA_FIGHT_HIT;}}}")
    s=rep(s,"/* The attack clip holds three swings. Each tap earns the next one; without another tap the swing ends just after it lands. */\n","/* Each tap during a swing earns the next one when it ends; otherwise the swing plays out its recovery, and a tap there starts again. */\n")
    return s
edit(r/"oa_combat.c",cc)
def test(s):
    s=rep(s,"c.clip_count==11&&","c.clip_count==16&&")
    s=rep(s,"if(f.play_player>=OA_FIGHT_ATTACK_A&&f.play_player<=OA_FIGHT_ATTACK_C)swings++;","if(oa_fight_is_swing(f.play_player))swings++;")
    return s
edit(r/"oa_character_test.c",test)
def scene(s):
    s=rep(s,'if(world&&c->world){AAsset *asset=AAssetManager_open(manager,"town_enemy.bin",AASSET_MODE_BUFFER);','if(world&&c->world&&!active_stream){AAsset *asset=AAssetManager_open(manager,"town_enemy.bin",AASSET_MODE_BUFFER);')
    s=rep(s,"if(playing&&!prof.on&&c.foe_ready&&c.collision_ready&&!interaction.window_open){oa_combat *f=&c.combat;char fight_error[256]=\"\";\n                    oa_combat_step(f,dt,movement.attack_requested&&focused,c.body.feet,c.character.facing,c.foe.feet);","""if(prof.fight&&playing){static float tap;if((tap-=dt)<=0){tap=(float)prof.fight*.01f;movement.attack_requested=1;}}
                if(playing&&(!prof.on||prof.fight)&&(c.foe_ready||active_actors)&&c.collision_ready&&!interaction.window_open){oa_combat *f=&c.combat;char fight_error[256]="";static const float nobody[3]={1e7f,1e7f,0};
                    oa_combat_step(f,dt,movement.attack_requested&&focused,c.body.feet,c.character.facing,c.foe_ready?c.foe.feet:nobody);
                    /* Moving breaks out of a recovery. */
                    if(f->player_clip>=OA_FIGHT_RECOVER&&movement.move_x*movement.move_x+movement.move_y*movement.move_y>.02f){f->player_clip=0;f->player_stage=0;f->queued=0;f->stop_player=1;}""")
    s=rep(s,"else if(f->foe!=OA_FOE_DEAD&&opem_controller_step(c.world,&c.body_config,&c.foe_body,0,0,dt,fight_error,sizeof(fight_error)))","else if(c.foe_ready&&f->foe!=OA_FOE_DEAD&&opem_controller_step(c.world,&c.body_config,&c.foe_body,0,0,dt,fight_error,sizeof(fight_error)))")
    s=rep(s,"if(now-c.foe_log_ms>1500){c.foe_log_ms=now;LOGI(\"Fight foe=","if(c.foe_ready&&now-c.foe_log_ms>1500){c.foe_log_ms=now;LOGI(\"Fight foe=")
    s=rep(s,"view.health=c->foe_ready?hud[0]:1.f;view.foe=c->foe_ready?hud[1]:-1.f;view.dead=c->foe_ready&&hud[2]>0;","view.health=hud[0];view.foe=c->foe_ready?hud[1]:-1.f;view.dead=hud[2]>0;")
    s=rep(s,"if(af.has_turn&&f->play_player>=OA_FIGHT_ATTACK_A&&f->play_player<=OA_FIGHT_ATTACK_C)","if(af.has_turn&&oa_fight_is_swing(f->play_player))")
    s=rep(s,'prof.fx=prop_int("debug.opem.fx",0);','prof.fx=prop_int("debug.opem.fx",0);prof.fight=prop_int("debug.opem.fight",0);')
    s,c=re.subn(r"(\bint [^;{}]*\bfx\b[^;{}]*;)",lambda m:m.group(1)+"int fight;",s,count=1)
    assert c==1
    return s
edit(r/"android_scene.c",scene)
def pack(s):return rep(s,"opem-amalur-scene-v0.31-arm64.apk","opem-amalur-scene-v0.32-arm64.apk")
edit(r/"package_android.py",pack)
def man(s):return rep(rep(s,'android:versionCode="33"','android:versionCode="34"'),'android:versionName="0.31.0"','android:versionName="0.32.0"')
edit(r/"AndroidManifest.xml",man)
print("ok")
