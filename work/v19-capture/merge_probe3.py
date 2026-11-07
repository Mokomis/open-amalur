"""Find the merge shader by what it must do: read a 256x16 table using the captured layout constants."""
import json, re
from pathlib import Path

root = Path.home() / "Documents" / "Opem Amalur"
shaders = root / "outputs/scene-v19/shaders"
prov = json.loads((root / "outputs/scene-v19/lighting-provenance.json").read_text(encoding="utf-8-sig"))
text = json.dumps(prov)
for m in re.finditer(r"[^\"]{0,160}(2D lookup|final lookup|merge)[^\"]{0,240}", text):
    print("PROV:", m.group(0)[:400])
for path in sorted(shaders.glob("*.asm")):
    body = path.read_text(errors="replace")
    code = [l for l in body.splitlines() if not l.startswith("//")]
    if not code or not code[0].startswith("ps_"):
        continue
    joined = "\n".join(code)
    names = re.findall(r"^//\s+(\w+)\s+texture\s", body, re.M)
    keyword = any(re.search("lut|lookup|color(correct|grade|transition)|bloom|merge|scene", n, re.I) for n in names)
    shape = "floor" in joined or "round_ni" in joined or "cb0[1].z" in joined and "cb0[1].w" in joined
    if keyword or (shape and "cb0[0].x" in joined and "cb0[2].x" in joined and len(code) < 90 and "cb4[" not in joined):
        print("---", path.stem, "lines", len(code), "textures", names)
        if len(code) < 90:
            print("\n".join(l for l in code if not l.startswith(("dcl_sampler", "dcl_temps", "dcl_input", "ps_"))))
