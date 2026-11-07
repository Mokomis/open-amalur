from pathlib import Path
f = Path.home() / "Documents/Opem Amalur/work/v19-host/android_scene.c"
t = f.read_bytes().decode("utf-8")
old = "eye[2]=c->body.feet[2]+OA_CAMERA_PIVOT-forward[2]*c->boom;\n"
if t.count(old) != 1: raise SystemExit("eye match %d" % t.count(old))
t = t.replace(old, "eye[2]=fmaxf(c->body.feet[2]+OA_CAMERA_PIVOT-forward[2]*c->boom,c->body.feet[2]+40.0f);\n")
f.write_bytes(t.encode("utf-8"))
print("patched")
