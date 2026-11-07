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
    s=rep(s,"world_programs[4];","world_programs[7];")
    s=rep(s,"{int wi;for(wi=0;wi<4;wi++)if(g->world_programs[wi])","{int wi;for(wi=0;wi<7;wi++)if(g->world_programs[wi])")
    s=rep(s,"{int wi,all=1;for(wi=0;wi<4;wi++){g->world_programs[wi]=","{int wi,all=1;for(wi=0;wi<7;wi++){g->world_programs[wi]=")
    s=rep(s,"for(v=0;v<4;v++){GLuint w=g->world_programs[v];","for(v=0;v<7;v++){GLuint w=g->world_programs[v];")
    s=rep(s,'glUniform1i(glGetUniformLocation(w,"shadow_on"),shadow_on);','glUniform1i(glGetUniformLocation(w,"shadow_on"),shadow_on);glUniform1f(glGetUniformLocation(w,"game_time"),(float)(monotonic_ms()%3600000)*.001f);')
    # A test aid to look at a chosen place.
    s=rep(s,"/* Test aid: debug.opem.tour holds the stick","""/* Test aid: debug.opem.at "x y z" moves the player there once. */
                if(playing&&active_stream&&c.collision_ready){static int moved;if(!moved){char at_prop[PROP_VALUE_MAX]={0};float at[3];moved=1;if(__system_property_get("debug.opem.at",at_prop)>0&&sscanf(at_prop,"%f %f %f",&at[0],&at[1],&at[2])==3){char why[128]="";opem_collision_world *near_world=oa_stream_collision_now(active_stream,at,why,sizeof(why));if(near_world){opem_collision_destroy(c.world);c.world=near_world;if(opem_controller_spawn(c.world,&c.body_config,at,&c.body,why,sizeof(why))){memcpy(c.character.feet,c.body.feet,sizeof(c.body.feet));LOGI("Moved to (%.0f %.0f %.0f)",c.body.feet[0],c.body.feet[1],c.body.feet[2]);}else LOGE("Move rejected: %s",why);}}}}
                /* Test aid: debug.opem.tour holds the stick""")
    return s
edit(r/"android_scene.c",scene)
def pack(s):return rep(s,"opem-amalur-scene-v0.32-arm64.apk","opem-amalur-scene-v0.33-arm64.apk")
edit(r/"package_android.py",pack)
def man(s):return rep(rep(s,'android:versionCode="34"','android:versionCode="35"'),'android:versionName="0.32.0"','android:versionName="0.33.0"')
edit(r/"AndroidManifest.xml",man)
def cmd(s):
    s=rep(s,"echo VEGGIE >> work\\v20-char\\rebuild.log","echo CUTOFFS >> work\\v20-char\\rebuild.log\r\npython work\\v20-char\\build_cutoffs.py >> work\\v20-char\\rebuild.log 2>&1 || goto bad\r\necho VEGGIE >> work\\v20-char\\rebuild.log" if "\r\n" in s else "echo CUTOFFS >> work\\v20-char\\rebuild.log\npython work\\v20-char\\build_cutoffs.py >> work\\v20-char\\rebuild.log 2>&1 || goto bad\necho VEGGIE >> work\\v20-char\\rebuild.log")
    return s
f=R/"work/v20-char/rebuild.cmd";t=f.read_text();f.write_text(cmd(t))
t=f.read_text();a="python work\\v20-char\\route_probe.py"
assert a in t
f.write_text(t.replace(a,"python work\\v20-char\\build_route.py >> work\\v20-char\\rebuild.log 2>&1\npython work\\v20-char\\water_spots.py >> work\\v20-char\\rebuild.log 2>&1\n"+a,1))
print("ok")
