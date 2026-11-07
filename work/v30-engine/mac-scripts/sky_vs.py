import json, re
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
idx = json.loads((root / "outputs/scene-v19/shader-index.json").read_text())
print("PS", idx["eb22737fa46893d9"])
sd = root / "outputs/scene-v19/shaders"
out = []
for name, e in idx.items():
    if e.get("type") != "vs": continue
    b = (sd / f"{name}.asm").read_text(errors="replace")
    code = [l for l in b.splitlines() if not l.startswith("//") and l.strip()]
    d = dict(re.findall(r"dcl_output(?:_siv)? o(\d)\.(\w+)", b))
    v = " ".join(e.get("vars", []))
    if re.search(r"[Ss]ky|[Cc]loud|transition", v) or (len(code) < 45 and set(d) == set("0123")):
        out.append((name, len(code), d, e.get("vars"), code))
for name, n, d, v, code in sorted(out, key=lambda x: x[1])[:6]:
    print("=====", name, n, d, v)
    for l in code:
        if re.match(r"\s*(mov|mul|mad|add|dp|div|sub|rsq|sqrt|ret|dcl_input|dcl_constant)", l): print(l)
