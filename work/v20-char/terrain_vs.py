import json, re
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
idx = json.loads((root / "outputs/scene-v19/shader-index.json").read_text())
vs = [n for n, r in idx.items() if r.get("type") == "vs" and "g_terrainbuffer" in r.get("cbuffers", [])]
print(len(vs))
ps = [n for n, r in idx.items() if r.get("type") == "ps" and "g_terrainbuffer" in r.get("cbuffers", [])]
print("ps", len(ps))
vs.sort(key=lambda n: idx[n]["lines"])
for n in vs[:1]:
    body = (root / f"outputs/scene-v19/shaders/{n}.asm").read_text(errors="replace")
    a = body.index("cbuffer g_terrainbuffer") if "cbuffer g_terrainbuffer" in body else 0
    print(body[a:a + 900])
    print(body[body.index("// Input signature"):body.index("// Output signature")])
    print("\n".join(l for l in body.splitlines() if not l.startswith("//"))[:2800])
