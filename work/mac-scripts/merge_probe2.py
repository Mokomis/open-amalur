"""List small post-process shaders that use three or more 2D textures, and find table asset 1426979."""
from pathlib import Path

root = Path.home() / "Documents" / "Opem Amalur"
shaders = root / "outputs/scene-v19/shaders"
for path in sorted(shaders.glob("*.asm")):
    code = [l for l in path.read_text(errors="replace").splitlines() if not l.startswith("//")]
    if not code or not code[0].startswith("ps_"):
        continue
    text = "\n".join(code)
    tex2 = sum("dcl_resource_texture2d" in l for l in code)
    if "texture3d" in text or "texturecube" in text or "o1." in text or "cb4[" in text or tex2 < 3 or tex2 > 6 or len(code) > 75:
        continue
    print("---", path.stem, "lines", len(code), "tex", tex2)
    print("\n".join(l for l in code if not l.startswith(("dcl_sampler", "dcl_temps", "dcl_input", "dcl_output", "ps_"))))
print("=== Files for 1426979")
for p in (root / "work").rglob("1426979*"):
    print(p, p.stat().st_size)
print("=== How 1525613 was found")
for folder in ("work/v19-lighting", "work/v19-host"):
    for p in (root / folder).glob("*.py"):
        for n, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            if "1525613" in line or "pak" in line.lower() and "open" in line.lower():
                print(p.name, n, line.strip()[:200])
for p in (root / "work").rglob("1525613*"):
    print(p, p.stat().st_size)
