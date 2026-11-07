from pathlib import Path
host = Path.home() / "Documents/Opem Amalur/work/v19-host"
f = host / "android_scene.c"; t = f.read_bytes().decode("utf-8")
assert t.count('prop_int("debug.opem.far",640)') == 1 and t.count("static float stream_far=64000.0f;") == 1
t = t.replace('prop_int("debug.opem.far",640)', 'prop_int("debug.opem.far",1000)').replace("static float stream_far=64000.0f;", "static float stream_far=100000.0f;")
f.write_bytes(t.encode("utf-8"))
f = host / "package_android.py"; t = f.read_text(); a = "str(root/'work/v22-stress/pack')"; assert t.count(a) == 1; f.write_text(t.replace(a, "str(root/'work/v22-stress/zone-pack')")); print("ok")
