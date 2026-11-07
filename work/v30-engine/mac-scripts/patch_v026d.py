from pathlib import Path
f = Path.home() / "Documents/Opem Amalur/work/v19-host/android_scene.c"; t = f.read_bytes().decode("utf-8")
old = "if(prof.walk&&playing)movement.move_y=1.f;"
assert t.count(old) == 1
t = t.replace(old, "/* Test aid: debug.opem.walk is a heading in degrees plus one. */\n                if(prof.walk&&playing){movement.move_y=1.f;c.walk_yaw=(float)(prof.walk-1)*.01745329f;}")
f.write_bytes(t.encode("utf-8")); print("ok")
