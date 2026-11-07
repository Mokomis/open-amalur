from pathlib import Path
r=Path.home()/"Documents/Opem Amalur/work/v19-host"
def edit(name,fn):
    f=r/name;s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n");s=fn(s)
    if crlf:s=s.replace("\n","\r\n")
    f.write_bytes(s.encode())
def rep(s,a,b):
    assert a in s,a[:70]
    return s.replace(a,b,1)
def scene(s):
    s=rep(s,'#include "oa_post.h"\n','#include "oa_post.h"\n#include "oa_actors.h"\n')
    s=rep(s,"static oa_stream *active_stream;","static oa_actors *active_actors;static oa_stream *active_stream;")
    s=rep(s," exploration_overlay_close(&g->overlay);oa_ui_close(&g->ui);"," oa_actors_gpu_close(active_actors);exploration_overlay_close(&g->overlay);oa_ui_close(&g->ui);")
    s=rep(s,"if(active_stream)oa_stream_update(active_stream,eye);","if(active_stream)oa_stream_update(active_stream,eye);oa_actors_gpu_update(active_actors,&g->character);")
    s=rep(s,"if(c->foe_ready)oa_character_gpu_draw(&g->foe,&c->foe,shadow_matrix,0,.5f);","if(c->foe_ready)oa_character_gpu_draw(&g->foe,&c->foe,shadow_matrix,0,.5f);oa_actors_draw_shadow(active_actors,shadow_matrix,c->body.feet);")
    s=rep(s,"if(c->foe_ready&&!(prof.skip&4))oa_character_gpu_draw(&g->foe,&c->foe,matrix,room_lighting,.5f);","if(c->foe_ready&&!(prof.skip&4))oa_character_gpu_draw(&g->foe,&c->foe,matrix,room_lighting,.5f);if(!(prof.skip&4))oa_actors_draw(active_actors,matrix,room_lighting);")
    s=rep(s,"view.room_lighting=room_lighting;","view.room_lighting=room_lighting;{float focus_hp;const char *focus_name;if(oa_actors_focus(active_actors,c->body.feet,&focus_hp,&focus_name)){view.foe=focus_hp;view.foe_name=focus_name;}}")
    # The zone's own people replace the fixed townsfolk outdoors.
    s=rep(s,'if(world){AAsset *asset=AAssetManager_open(manager,"town_npcs.bin",AASSET_MODE_BUFFER);','if(world&&!active_stream){AAsset *asset=AAssetManager_open(manager,"town_npcs.bin",AASSET_MODE_BUFFER);')
    s=rep(s,"oa_stream_close(active_stream);active_stream=NULL;","oa_actors_close(active_actors);active_actors=NULL;oa_stream_close(active_stream);active_stream=NULL;")
    s=rep(s,"if(world)active_stream=oa_stream_open(manager);","if(world){active_stream=oa_stream_open(manager);active_actors=oa_actors_open(manager);}")
    i=s.rindex("oa_stream_close(active_stream);active_stream=NULL;");s=s[:i]+"oa_actors_close(active_actors);active_actors=NULL;"+s[i:]
    s=rep(s,"movement.attack_requested=0;\n                if(prof.tour&&active_stream&&playing)","""if(playing&&active_actors&&c.collision_ready&&!interaction.window_open){oa_combat *f=&c.combat;oa_actors_frame af;
                     oa_actors_update(active_actors,c.world,c.body.feet,c.character.facing,!f->player_dead,f->swing_landed?f->player_damage:0.f,dt,&af);
                     if(af.has_turn&&f->play_player>=OA_FIGHT_ATTACK_A&&f->play_player<=OA_FIGHT_ATTACK_C)c.character.facing=af.turn_yaw;
                     /* Test runs measure the fight without ending it. */
                     if(af.damage>0&&!prof.on){f->play_player=-1;oa_combat_hurt_player(f,af.damage*f->foe_damage/9.f);if(f->play_player>=0)oa_character_play(&c.character,f->play_player,f->hold_player,f->play_player_rate);c.move_scale=f->player_dead||f->player_clip?0.f:1.f;}
                     if(af.kills){static char loot[64];unsigned coin=4+(unsigned)(rand()%12);menu.bag.gold+=coin;snprintf(loot,sizeof(loot),"%s slain, %u gold",af.killed,coin);oa_menu_status(&menu,loot);}}
                 movement.attack_requested=0;
                 if(prof.tour&&active_stream&&playing)""")
    s=rep(s,"if(prof.on){int64_t gap=prof.last?t2-prof.last:0;","if(prof.on&&prof.last&&t2-prof.last>40000000){LOGI(\"HITCH gap_ms=%.1f sim_ms=%.1f submit_ms=%.1f swap_ms=%.1f\",(t2-prof.last)/1e6,(prof_t0-prof.start)/1e6,(t1-prof_t0)/1e6,(t2-t1)/1e6);}\n      if(prof.on&&active_actors&&prof.frames==239){oa_actors_stats as;oa_actors_get_stats(active_actors,&as);LOGI(\"ACTORS total=%u near=%u moving=%u chasing=%u bodies=%u drawn=%u models=%u rays=%u update_ms=%.2f\",as.total,as.near_count,as.moving,as.chasing,as.slots,as.drawn,as.models,as.rays,as.update_ms);}\n      if(prof.on){int64_t gap=prof.last?t2-prof.last:0;")
    return s
edit("android_scene.c",scene)
def cm(s):
    s=rep(s,"oa_post.c","oa_post.c oa_actors.c oa_actor_ai.c")
    return s
edit("android_scene.cmake",cm)
def cml(s):
    s=rep(s,"add_executable(oa-character-test oa_character_test.c","add_executable(oa-actor-ai-test oa_actor_ai_test.c oa_actor_ai.c)\nif(NOT WIN32)\n  target_link_libraries(oa-actor-ai-test PRIVATE m)\nendif()\nadd_executable(oa-character-test oa_character_test.c")
    return s
edit("CMakeLists.txt",cml)
def val(s):
    s=rep(s,"--target amalur-exploration-input-test oa-character-test oa-menu-test","--target amalur-exploration-input-test oa-character-test oa-menu-test oa-actor-ai-test")
    s=rep(s,"work\\v19-host\\build-windows\\oa-menu-test.exe","work\\v19-host\\build-windows\\oa-actor-ai-test.exe > outputs\\scene-v19\\actor-tests.txt 2>&1\nif errorlevel 1 exit /b %errorlevel%\nwork\\v19-host\\build-windows\\oa-menu-test.exe")
    return s
edit("build_validate.cmd",val)
def pack(s):
    s=rep(s,"opem-amalur-scene-v0.28-arm64.apk","opem-amalur-scene-v0.29-arm64.apk")
    s=rep(s,"for _p in Path(_os.environ.get('OA_WORLD_DIR',","for _p in (root/'work/v23-actors').glob('*.bin'):files['assets/actors/'+_p.name]=_p\nfor _p in Path(_os.environ.get('OA_WORLD_DIR',")
    return s
edit("package_android.py",pack)
def man(s):
    return rep(rep(s,'android:versionCode="30"','android:versionCode="31"'),'android:versionName="0.28.0"','android:versionName="0.29.0"')
edit("AndroidManifest.xml",man)
print("ok")
