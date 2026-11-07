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
    s=rep(s,'#include "oa_actors.h"\n','#include "oa_actors.h"\n#include "oa_audio.h"\n')
    s=rep(s,"static unsigned tour_frames,","static oa_audio *active_audio;static int snd_foot=-1,snd_use=-1,snd_hit=-1,snd_die=-1;static unsigned tour_frames,")
    s=rep(s,"if(world){active_stream=oa_stream_open(manager);active_actors=oa_actors_open(manager);}","if(world){active_stream=oa_stream_open(manager);active_actors=oa_actors_open(manager);if(!active_audio)active_audio=oa_audio_open(manager);oa_actors_use_audio(active_actors,active_audio);snd_foot=oa_audio_group(active_audio,\"foot_grass\");snd_use=oa_audio_group(active_audio,\"blade_use\");snd_hit=oa_audio_group(active_audio,\"blade_hit\");snd_die=oa_audio_group(active_audio,\"player_die\");{static int bed;if(!bed){bed=1;oa_audio_loop(active_audio,oa_audio_group(active_audio,\"bed_forest\"),6.f);}}}")
    # Footsteps from the clip's own cycle; swing, hit and death from the fight.
    import re as _re
    s,_c=_re.subn(r"movement\.attack_requested=0;\n( *)if\(prof\.tour&&active_stream&&playing\)",lambda m:'if(playing&&active_audio&&c.collision_ready){const oa_combat *f=&c.combat;float mv=movement.move_x*movement.move_x+movement.move_y*movement.move_y;static float phase;static int was_dead;\n                    oa_audio_listener(active_audio,c.body.feet,c.walk_yaw);\n                    if(mv>.01f&&c.body.grounded){int run=mv>.5f;const oa_char_clip *k=c.character.clips+(run?OA_CLIP_RUN:OA_CLIP_WALK);float seconds=(float)(k->frames-1)/k->fps,was=phase;float rate=(run?420.f:420.f*sqrtf(mv))/(c.character.clip_speed[run?OA_CLIP_RUN:OA_CLIP_WALK]>1.f?c.character.clip_speed[run?OA_CLIP_RUN:OA_CLIP_WALK]:420.f);phase=fmodf(phase+dt*rate/seconds*2.f,1.f);if(phase<was)oa_audio_play(active_audio,snd_foot,NULL,.35f,1.f);}\n                    if(oa_fight_is_swing(f->play_player))oa_audio_play(active_audio,snd_use,NULL,.6f,1.f);\n                    if(f->swing_landed&&(f->foe_struck))oa_audio_play(active_audio,snd_hit,NULL,.7f,1.f);\n                    if(f->player_dead&&!was_dead)oa_audio_play(active_audio,snd_die,NULL,.8f,1.f);was_dead=f->player_dead;}\n'+"movement.attack_requested=0;\n"+m.group(1)+"if(prof.tour&&active_stream&&playing)",s,count=1);assert _c==1
    s=rep(s,"if(af.kills){static char loot[64];","if(af.hits&&active_audio)oa_audio_play(active_audio,snd_hit,NULL,.7f,1.f);if(af.kills){static char loot[64];")
    s=rep(s,'capsules=%u paths=%u update_ms=%.2f",','capsules=%u paths=%u update_ms=%.2f audio_voices=%u audio_mix_ms=%.3f audio_xruns=%u",')
    s=rep(s,"as.capsules,as.paths,as.update_ms)","as.capsules,as.paths,as.update_ms,audio_now.voices,audio_now.mix_ms,audio_now.underruns)")
    s=rep(s,"{oa_actors_stats as;oa_actors_get_stats(active_actors,&as);","{oa_actors_stats as;oa_audio_stats audio_now;oa_actors_get_stats(active_actors,&as);oa_audio_get_stats(active_audio,&audio_now);")
    s=rep(s,"playing=","oa_audio_set_active(active_audio,resumed&&focused);playing=") if False else s
    i=s.rindex("oa_actors_close(active_actors);active_actors=NULL;");s=s[:i]+"oa_audio_close(active_audio);active_audio=NULL;"+s[i:]
    return s
edit(r/"android_scene.c",scene)
def fr(s):
    s=rep(s,"typedef struct oa_actors_frame{float damage,turn_yaw;int has_turn,kills;const char *killed;}oa_actors_frame;","typedef struct oa_actors_frame{float damage,turn_yaw;int has_turn,kills,hits;const char *killed;}oa_actors_frame;")
    return s
edit(r/"oa_actors.h",fr)
def fr2(s):
    return rep(s,"oa_actor_hurt(x,t,swing_damage,&e);if(e.stop||e.play>=0||e.hold)handle(a,x,&e);","oa_actor_hurt(x,t,swing_damage,&e);out->hits++;if(e.stop||e.play>=0||e.hold||e.died)handle(a,x,&e);")
edit(r/"oa_actors.c",fr2)
def pack(s):return rep(s,"for _p in (root/'work/v23-actors').glob('*.bin'):","for _p in (root/'work/v23-audio').glob('*.bin'):files['assets/audio/'+_p.name]=_p\nfor _p in (root/'work/v23-actors').glob('*.bin'):")
edit(r/"package_android.py",pack)
print("ok")
