from pathlib import Path
r=Path.home()/"Documents/Opem Amalur/work/v19-host";f=r/"android_scene.c";s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n")
a=s.index("/* Test aid: debug.opem.tour walks the player at that speed");b=s.index("if(playing)oa_npcs_update(&c.npcs,dt);")
s=s[:a]+'''/* Test aid: debug.opem.tour holds the stick along a route computed from the zone's collision, so everything below runs as it does in play. */
                if(prof.tour&&playing&&active_stream&&c.collision_ready){static float *route,wait,here,stuck,last[2];static uint32_t count,next;float dx,dy,d;
                    if(!route){AAsset *as=AAssetManager_open(s->activity->assetManager,"actors/route.bin",AASSET_MODE_BUFFER);if(as){const uint8_t *rb=(const uint8_t*)AAsset_getBuffer(as);memcpy(&count,rb,4);route=(float*)malloc((size_t)count*12u);if(route)memcpy(route,rb+4,(size_t)count*12u);AAsset_close(as);LOGI("TOUR route waypoints=%u",count);}}
                    tour_frames++;if(!c.body.grounded)tour_air++;
                    if(route&&next<count){const float *w=route+next*3;dx=w[0]-c.body.feet[0];dy=w[1]-c.body.feet[1];d=sqrtf(dx*dx+dy*dy);here+=dt;
                        {float mx=c.body.feet[0]-last[0],my=c.body.feet[1]-last[1];if(here>.5f){stuck=mx*mx+my*my<30.f*30.f?stuck+here:0;here=0;last[0]=c.body.feet[0];last[1]=c.body.feet[1];}}
                        movement.move_y=0;movement.move_x=0;
                        if(d<(w[2]>0?150.f:220.f)){if(w[2]>0){if((wait+=dt)>6.f){wait=0;next++;tour_reached++;stuck=0;}}else{next++;stuck=0;}}
                        else{float t=remainderf(atan2f(dy,dx)-c.walk_yaw,6.283185307f),turn=dt*6.f;c.walk_yaw=remainderf(c.walk_yaw+(t>turn?turn:t<-turn?-turn:t),6.283185307f);movement.move_y=1.f;}
                        /* Past a blocked waypoint, on to the next. */
                        if(stuck>6.f){next++;stuck=0;tour_gave_up++;}
                        if(next>=count){next=0;}
                        c.walk_pitch=-.12f;}}
                '''+s[b:]
A="if(prof.tour&&active_stream&&playing){movement.look_dx=movement.look_dy=0;}else if(focused&&!interaction.window_open&&playing)exploration_update(&c,&movement,dt);"
assert A in s
s=s.replace(A,"if(prof.tour&&active_stream&&playing)movement.look_dx=movement.look_dy=0;\n                if(focused&&!interaction.window_open&&playing)exploration_update(&c,&movement,dt);",1)
if crlf:s=s.replace("\n","\r\n")
f.write_bytes(s.encode());print("ok")
