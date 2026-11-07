"""Report merge shader code, global constants and which authored regions match the live values."""
import json, re, struct, sys
from pathlib import Path

root = Path.home() / "Documents" / "Opem Amalur"
shaders = root / "outputs/scene-v19/shaders"
run = Path(sys.argv[1])
f = json.loads((run / "frame.json").read_text())
blob = (run / "frame.bin").read_bytes()
g = [e for e in f["events"] if e["e"] == "cbdata" and e["size"] == 1376][-1]
data = blob[g["at"]:g["at"] + 1376]

sample = next(p for p in sorted(shaders.glob("*.asm")) if "g_globalbuffer" in p.read_text(errors="replace"))
text = sample.read_text(errors="replace")
start = text.index("cbuffer g_globalbuffer")
members = re.findall(r"^//\s+(\w+)\s+(\w+)(\[\d+\])?;\s*// Offset:\s+(\d+)", text[start:text.index("// Resource Bindings")], re.M)
if not members:
    print(text[start:start + 2500])
print("=== g_global")
for kind, name, arr, off in members:
    off = int(off)
    if "PAD" in name:
        continue
    width = {"float": 1, "float2": 2, "float3": 3, "float4": 4, "float4x4": 16, "float3x4": 12}.get(kind, 4)
    count = int(arr[1:-1]) if arr else 1
    vals = struct.unpack_from("<%df" % min(width * count, 16), data, off)
    print("%5d %-8s %-30s %s" % (off, kind, name + (arr or ""), [round(v, 5) for v in vals]))
(run / "g_global.bin").write_bytes(data)

index = json.loads((root / "outputs/scene-v19/shader-index.json").read_text())
print("=== shaders using g_constantDatabuffer with several textures")
for name, row in index.items():
    if row.get("type") == "ps" and "g_constantDatabuffer" in row.get("cbuffers", []) and len(row.get("res", [])) >= 3:
        print(name, row["lines"], [r for r in row["res"] if not r.startswith("g_")])
        if row["lines"] < 140:
            body = (shaders / (name + ".asm")).read_text(errors="replace")
            print("\n".join(l for l in body.splitlines() if not l.startswith("//"))[:2600])
