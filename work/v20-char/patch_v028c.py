from pathlib import Path
f = Path.home() / "Documents/Opem Amalur/work/v19-host/android_scene.c"; t = f.read_bytes().decode("utf-8")
def rep(a, b):
    global t
    if t.count(a) != 1: raise SystemExit("no match " + a[:70])
    t = t.replace(a, b)
rep("tour,far_m,tour_m,live,fx;", "tour,far_m,tour_m,live,fx,heading;")
rep('prof.fx=prop_int("debug.opem.fx",0);}', 'prof.fx=prop_int("debug.opem.fx",0);prof.heading=prop_int("debug.opem.heading",0);}')
rep("                if(prof.walk&&playing){", "                /* Test aid: debug.opem.heading fixes the view in degrees plus one, so runs are comparable. */\n                if(prof.heading&&playing){c.walk_yaw=(float)(prof.heading-1)*.01745329f;c.walk_pitch=-.05f;}\n                if(prof.walk&&playing){")
f.write_bytes(t.encode("utf-8")); print("ok")
