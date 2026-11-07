from pathlib import Path
f = Path.home() / "Documents/Opem Amalur/work/v19-host/android_scene.c"; t = f.read_bytes().decode("utf-8")
def rep(a, b):
    global t
    if t.count(a) != 1: raise SystemExit("no match " + a[:70])
    t = t.replace(a, b)
rep("static oa_stream *active_stream;", "static oa_stream *active_stream;static float stream_far=64000.0f;")
rep("far_plane=active_stream&&c->walking?120000.0f:", "far_plane=active_stream&&c->walking?stream_far*1.6f:")
rep("static struct{int on,skip,scale,crowd,shadow,walk,tour;", "static struct{int on,skip,scale,crowd,shadow,walk,tour,far_m,tour_m;")
rep('prof.tour=prop_int("debug.opem.tour",0);}', 'prof.tour=prop_int("debug.opem.tour",0);prof.far_m=prop_int("debug.opem.far",640);prof.tour_m=prop_int("debug.opem.tourr",320);stream_far=(float)prof.far_m*100.0f;}')
rep("    if(world)active_stream=oa_stream_open(manager);\n", "    if(world)active_stream=oa_stream_open(manager);\n    if(active_stream)oa_stream_set_far(active_stream,stream_far);\n") if "    if(world)active_stream=oa_stream_open(manager);\n" in t else rep("    if(world)active_stream=oa_stream_open(manager);\r\n", "    if(world)active_stream=oa_stream_open(manager);\r\n    if(active_stream)oa_stream_set_far(active_stream,stream_far);\r\n")
rep("float R=32000.f,dir[3]", "float R=(float)prof.tour_m*100.f,dir[3]")
f.write_bytes(t.encode("utf-8")); print("ok")
