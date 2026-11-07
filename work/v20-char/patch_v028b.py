from pathlib import Path
f = Path.home() / "Documents/Opem Amalur/work/v19-host/android_scene.c"; t = f.read_bytes().decode("utf-8")
a = 'glUniform2f(glGetUniformLocation(w,"fog"),oa_live_fog_start,oa_live_fog_density);'
assert t.count(a) == 1
t = t.replace(a, '/* The fog value is real; its scale is authored, since the mapping into the game\'s fog constants is not recovered. */glUniform2f(glGetUniformLocation(w,"fog"),0.f,oa_live_fog_density*1.2e-7f);')
f.write_bytes(t.encode("utf-8")); print("ok")
