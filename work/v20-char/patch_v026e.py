from pathlib import Path
f = Path.home() / "Documents/Opem Amalur/work/v19-host/android_scene.c"; t = f.read_bytes().decode("utf-8")
a = "if(active_stream&&prof.shadow&&c->walking&&g->program){"
assert t.count(a) == 1
t = t.replace(a, "if(active_stream&&(prof.shadow||menu->settings.shadows)&&c->walking&&g->program){")
a = "float half=(float)prof.shadow*100.0f,"
assert t.count(a) == 1
t = t.replace(a, "float half=(float)(prof.shadow?prof.shadow:60)*100.0f,")
t = t.replace("/* Sun shadow map around the player, a stress-test switch until its cost is settled. */", "/* Sun shadow map around the player. Filtering and range are authored host choices. */")
f.write_bytes(t.encode("utf-8")); print("ok")
