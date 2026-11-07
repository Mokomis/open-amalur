from pathlib import Path
r=Path.home()/"Documents/Opem Amalur/work/v19-host";f=r/"android_scene.c";s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n")
a=s.index("/* Test aid: debug.opem.tour flies the player in a wide loop to force streaming. */");b=s.index("if(playing)oa_npcs_update(&c.npcs,dt);")
s=s[:a]+'''/* Test aid: debug.opem.tour walks the player at that speed between the zone's encounters, waiting a few seconds at each. */
                if(prof.tour&&playing&&active_stream&&c.collision_ready){static float stop[3],wait;static int have;float dx=stop[0]-c.body.feet[0],dy=stop[1]-c.body.feet[1],d=sqrtf(dx*dx+dy*dy),dir[3]={0,0,-1},top[3],hit=0,move=(float)prof.tour*dt;
                    if(!have||(d<100.f&&(wait-=dt)<=0)){have=oa_actors_next_stop(active_actors,c.body.feet,stop);wait=6.f;}
                    else if(d>=100.f){if(move>d)move=d;c.body.feet[2]+=(stop[2]-c.body.feet[2])*move/d;c.body.feet[0]+=dx/d*move;c.body.feet[1]+=dy/d*move;c.walk_yaw=atan2f(dy,dx);}
                    top[0]=c.body.feet[0];top[1]=c.body.feet[1];top[2]=c.body.feet[2]+3000.f;if(opem_collision_ray(c.world,top,dir,8000.f,&hit)&&hit<8000.f)c.body.feet[2]=top[2]-hit;
                    memcpy(c.character.feet,c.body.feet,sizeof(c.body.feet));c.character.facing=c.walk_yaw;oa_character_animate(&c.character,d>=100.f?1.f:0.f,d>=100.f?(float)prof.tour:0.f,dt);oa_character_pose(&c.character);}
                '''+s[b:]
if crlf:s=s.replace("\n","\r\n")
f.write_bytes(s.encode());print("ok")
