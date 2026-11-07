from pathlib import Path
f = Path.home() / "Documents/Opem Amalur/work/v19-host/android_scene.c"; t = f.read_bytes().decode("utf-8")
old = 'else LOGE("World %d collision unavailable",world);'
assert t.count(old) == 1
t = t.replace(old, 'else LOGE("World %d collision unavailable: %s",world,error);')
old2 = 'const float *arrive=c->spawn_hint;char error[256];'
assert t.count(old2) == 1
t = t.replace(old2, 'const float *arrive=c->spawn_hint;char error[256]="mesh load failed";')
f.write_bytes(t.encode("utf-8")); print("ok")
