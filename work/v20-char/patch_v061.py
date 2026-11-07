from pathlib import Path
import re
root=Path.home()/"Documents/Opem Amalur";h=root/"work/v19-host"
t=(h/"oa_sky.c").read_text(encoding="utf-8")
m=re.search(r"vec3\(\.4196,\s*\.3608,\s*\.2235\)|vec3\(0?\.4196[^)]*\)",t);print("found",m.group(0) if m else None)
i=m.start();print(repr(t[max(0,i-300):i+200]))
print([l[:200] for l in t.splitlines() if "uniform" in l][:6]);print([l[:220] for l in t.splitlines() if "glGetUniformLocation" in l][:6]);print([l[:220] for l in t.splitlines() if "glUniform" in l][:8])
print((h/"oa_sky.h").read_text(encoding="utf-8")[:1200])
