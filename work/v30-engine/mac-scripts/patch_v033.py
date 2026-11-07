from pathlib import Path
r=Path.home()/"Documents/Opem Amalur/work/v19-host";f=r/"android_scene.c";s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n")
a=s.index("/* Test aid: debug.opem.tour walks the player at that speed");b=s.index("if(playing)oa_npcs_update(&c.npcs,dt);")
s=s[:a]+'''/* Test aid: debug.opem.tour walks the player at that speed between the zone's encounters through the real controller and collision, as a stick would. */
                if(prof.tour&&playing&&active_stream&&c.collision_ready){static float stop[3],wait,leg,stuck,detour,side=1.f;static int have;float dx=stop[0]-c.body.feet[0],dy=stop[1]-c.body.feet[1],d=sqrtf(dx*dx+dy*dy),was[2]={c.body.feet[0],c.body.feet[1]},moved=0;char why[64];
                    leg+=dt;tour_frames++;
                    if(!have||(d<250.f&&(wait-=dt)<=0)||leg>90.f){if(have){if(leg>90.f)tour_gave_up++;else tour_reached++;}have=oa_actors_next_stop(active_actors,c.body.feet,stop);wait=6.f;leg=0;detour=0;}
                    else{float vx=0,vy=0,speed=(float)prof.tour>c.body_config.max_speed?c.body_config.max_speed:(float)prof.tour;
                        if(d>=250.f){float aim=atan2f(dy,dx);if(detour>0){aim+=side*1.1f;detour-=dt;}vx=cosf(aim)*speed;vy=sinf(aim)*speed;}
                        if(opem_controller_step(c.world,&c.body_config,&c.body,vx,vy,dt>.1f?.1f:dt,why,sizeof(why))){float mx=c.body.feet[0]-was[0],my=c.body.feet[1]-was[1];moved=sqrtf(mx*mx+my*my)/(dt>0?dt:1);
                            if(d>=250.f){stuck=moved<speed*.3f?stuck+dt:0;if(stuck>.4f){detour=1.2f;side=-side;stuck=0;tour_detours++;}}
                            if(moved>10.f){float t=remainderf(atan2f(my,mx)-c.walk_yaw,6.283185307f),turn=dt*6.f;c.walk_yaw=remainderf(c.walk_yaw+(t>turn?turn:t<-turn?-turn:t),6.283185307f);}}
                        if(!c.body.grounded)tour_air++;}
                    memcpy(c.character.feet,c.body.feet,sizeof(c.body.feet));c.character.facing=c.walk_yaw;oa_character_animate(&c.character,moved>10.f?moved/c.body_config.max_speed:0.f,moved,dt);oa_character_pose(&c.character);}
                '''+s[b:]
A="static oa_actors *active_actors;"
assert A in s
s=s.replace(A,"static unsigned tour_frames,tour_air,tour_reached,tour_gave_up,tour_detours;"+A,1)
A='if(prof.on&&active_actors&&prof.frames==239){'
assert A in s
s=s.replace(A,'if(prof.on&&prof.tour&&prof.frames==239)LOGI("TOUR frames=%u airborne=%u reached=%u gave_up=%u detours=%u feet=(%.0f %.0f %.0f)",tour_frames,tour_air,tour_reached,tour_gave_up,tour_detours,c->body.feet[0],c->body.feet[1],c->body.feet[2]);'+A,1)
if crlf:s=s.replace("\n","\r\n")
f.write_bytes(s.encode());print("ok")
