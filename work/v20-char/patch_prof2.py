from pathlib import Path
f = Path.home() / "Documents/Opem Amalur/work/v19-host/android_scene.c"
t = f.read_bytes().decode("utf-8")
a = t.index("/* Stress-test instrumentation"); z = t.index("static int graphics_draw(graphics *g,")
block = t[a:z]; t = t[:a] + t[z:]
i = t.index("static int graphics_open(")
t = t[:i] + block + t[i:]
if "#include <time.h>" not in t: t = t.replace('#include "oa_menu.h"\n', '#include "oa_menu.h"\n#include <time.h>\n', 1)
f.write_bytes(t.encode("utf-8")); print("moved")
m = Path.home() / "Documents/Opem Amalur/work/v09-textures/material_package.py"
print([l for l in m.read_text().splitlines() if "MAX_VERTICES" in l][:2])
