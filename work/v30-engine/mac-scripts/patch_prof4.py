from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
f = root / "work/v19-host/android_scene.c"; t = f.read_bytes().decode("utf-8")
def rep(a, b):
    global t
    if t.count(a) != 1: raise SystemExit("no match " + a[:70])
    t = t.replace(a, b)
rep("static struct{int on,skip,scale;", "static struct{int on,skip,scale,crowd;")
rep('prof.scale=prop_int("debug.opem.scale",100);}', 'prof.scale=prop_int("debug.opem.scale",100);prof.crowd=prop_int("debug.opem.crowd",1);}')
rep("if(!(prof.skip&4)){unsigned p;for(p=0;p<c->npcs.count;p++)oa_character_gpu_draw(&g->people[p],c->npcs.people+p,matrix,room_lighting,.5f);}", "if(!(prof.skip&4)){unsigned p;int n;for(n=0;n<prof.crowd;n++)for(p=0;p<c->npcs.count;p++)oa_character_gpu_draw(&g->people[p],c->npcs.people+p,matrix,room_lighting,.5f);}")
f.write_bytes(t.encode("utf-8"))
b = root / "work/v20-char/build_town.py"; x = b.read_text()
old = "RADIUS, TEXTURE_LIMIT, STEP = float(sys.argv[1]) if len(sys.argv) > 1 else 6000.0, 256, 100.0"
assert x.count(old) == 1
b.write_text(x.replace(old, "RADIUS, TEXTURE_LIMIT, STEP = float(sys.argv[1]) if len(sys.argv) > 1 else 6000.0, int(__import__('os').environ.get('OA_TEXTURE_LIMIT', 256)), 100.0"))
print("ok")
