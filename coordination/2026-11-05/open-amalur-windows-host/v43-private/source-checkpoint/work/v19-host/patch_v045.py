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
    a=s.index('_c = ["human_idle_01"');b=s.index("\n",a)
    s=s[:a]+'_c = ["human_idle_01", "human_walk_01", "human_run_01", "human_sword_attack_x_02", "human_sword_attack_xx_02", "human_sword_attack_xxx_02", "human_norreacfrt", "human_Death_01", "human_sword_idle_01", "human_walk_01", "human_run_01", "human_sword_attack_xxxx_02"]'+s[b:]
    s=rep(s,"# From the Player, Player_Weapon_Sword and Player_Reactions motion sets. 0 to 2 explore; 3 to 5 and 11 are the combo swings; 6 reacts, 7 dies; 8 to 10 carry the sword, which only changes the idle; 12 to 15 recover from each swing.","# From the Player, Player_Weapon_Sword and Player_Reactions motion sets. 0 to 2 explore; 3 to 5 and 11 are the combo swings; 6 reacts, 7 dies; 8 to 10 carry the sword, which only changes the idle.\n# The swings are the game's _02 chain. Its _01 alternates carry 52 joints and do not decode correctly with this rig yet.")
    a=s.index("    # Some clips carry 52 joints.");b=s.index("    for i in range(frames * j):\n",a)
    s=s[:a]+'    if clip_joints_of(cid) != j:\n        raise SystemExit(f"{name}: {clip_joints_of(cid)} joints, rig {j}")\n'+s[b:]
    s=rep(s,'v = struct.unpack_from("<7f", b, 12 + i * 48) if i % j < clip_joints and i % j not in broken else struct.unpack_from("<7f", main, rest + (i % j) * 48)','v = struct.unpack_from("<7f", b, 12 + i * 48)')
    s=rep(s,'if "_attack_" not in name or name.endswith("_02"):','if "_attack_" not in name:')
    return s
edit(R/"work/v20-char/build_character.py",bc)
def ch2(s):
    s=rep(s,",OA_FIGHT_ATTACK_D=11,OA_FIGHT_RECOVER=12};\n/* The game's combo: each swing either runs into the next or into its own recovery. */",",OA_FIGHT_ATTACK_D=11};\n/* The game's combo. */")
    s=rep(s," int player_clip,player_dead,queued,player_stage;\n"," int player_clip,player_dead,queued,player_stage;\n /* When the current swing has landed and may be cut short; 0 until then. */\n float player_free_at;\n")
    return s
edit(r/"oa_combat.h",ch2)
def cc(s):
    s=rep(s,"#define PLAYER_RATE 1.f\n","#define PLAYER_RATE 1.f\n#define CHAIN_AFTER .2f\n")
    s=rep(s,"  if(attack&&oa_fight_is_swing(c->player_clip))c->queued=1;\n  else if(attack&&c->player_clip>=OA_FIGHT_RECOVER)c->player_time=c->player_length,c->queued=2;\n","  if(attack&&oa_fight_is_swing(c->player_clip))c->queued=1;\n")
    s=rep(s,"   c->swing_landed=1;\n","   c->swing_landed=1;c->player_free_at=c->player_time+CHAIN_AFTER;\n")
    a=s.index("  if(c->player_time>=c->player_length){\n   static const int next[4]");b=s.index(" else if(attack){c->player_stage=0;start_swing(c,OA_FIGHT_ATTACK_A);}")
    s=s[:a]+"""  {static const int next[4]={OA_FIGHT_ATTACK_A,OA_FIGHT_ATTACK_B,OA_FIGHT_ATTACK_C,OA_FIGHT_ATTACK_D};int free=c->player_free_at>0&&c->player_time>=c->player_free_at;
   if(free&&c->queued&&c->player_stage<3&&oa_fight_is_swing(c->player_clip)){c->player_stage++;start_swing(c,next[c->player_stage]);}
   else if(c->player_time>=c->player_length){if(c->queued&&oa_fight_is_swing(c->player_clip)){c->player_stage=0;start_swing(c,OA_FIGHT_ATTACK_A);}else{c->queued=0;c->player_clip=0;c->player_stage=0;c->player_free_at=0;c->stop_player=1;}}}}
"""+s[b:]
    s=rep(s,"static void start_swing(oa_combat *c,int clip){c->player_clip=clip;c->player_time=0;","static void start_swing(oa_combat *c,int clip){c->player_clip=clip;c->player_time=0;c->player_free_at=0;")
    s=rep(s," c->player_locked=c->player_dead||c->player_clip;"," c->player_locked=c->player_dead||(c->player_clip&&!(c->player_free_at>0&&c->player_time>=c->player_free_at));")
    s=rep(s,"/* Each tap during a swing earns the next one when it ends; otherwise the swing plays out its recovery, and a tap there starts again. */\n","/* A tap during a swing earns the next one soon after the swing lands; the timing of that window is authored. */\n")
    return s
edit(r/"oa_combat.c",cc)
def test(s):return rep(s,"c.clip_count==16&&","c.clip_count==12&&")
edit(r/"oa_character_test.c",test)
def ch(s):return rep(s,"OA_CHAR_MAX_CLIPS=16,","OA_CHAR_MAX_CLIPS=12,")
edit(r/"oa_character.h",ch)
def scene(s):
    s=rep(s,"/* Moving breaks out of a recovery. */\n                    if(f->player_clip>=OA_FIGHT_RECOVER&&movement.move_x*movement.move_x+movement.move_y*movement.move_y>.02f){f->player_clip=0;f->player_stage=0;f->queued=0;f->stop_player=1;}","/* Moving breaks out of a swing that has landed. */\n                    if(oa_fight_is_swing(f->player_clip)&&!f->player_locked&&!f->queued&&movement.move_x*movement.move_x+movement.move_y*movement.move_y>.02f){f->player_clip=0;f->player_stage=0;f->player_free_at=0;f->stop_player=1;}")
    return s
edit(r/"android_scene.c",scene)
print("ok")
