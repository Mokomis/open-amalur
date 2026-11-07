from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
f = root / "work/v19-host/android_scene.c"; t = f.read_bytes().decode("utf-8")
old = "if(ns){prof.gpu+=ns;prof.gpu_n++;if(ns>prof.gpu_max)prof.gpu_max=ns;}}}"
assert t.count(old) == 1
t = t.replace(old, "if(ns&&ns<1000000000u){prof.gpu+=ns;prof.gpu_n++;if(ns>prof.gpu_max)prof.gpu_max=ns;}}{GLenum e=glGetError();static int told;if(e!=GL_NO_ERROR&&!told){told=1;LOGE(\"Profiler left GL error 0x%x\",e);}}}")
f.write_bytes(t.encode("utf-8"))
h = root / "work/v09-textures/scene_materials_v09.h"; x = h.read_text()
x = x.replace("SCENE_MATERIALS_V09_MAX_VERTICES 4000000u", "SCENE_MATERIALS_V09_MAX_VERTICES 8000000u").replace("SCENE_MATERIALS_V09_MAX_BYTES (128u*1024u*1024u)", "SCENE_MATERIALS_V09_MAX_BYTES (384u*1024u*1024u)"); h.write_text(x)
m = root / "work/v09-textures/material_package.py"; x = m.read_text(); m.write_text(x.replace("MAX_VERTICES=4000000", "MAX_VERTICES=8000000"))
print("ok")
