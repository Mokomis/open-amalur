"""Search exe and reference notes for the animation clip decoder; dump a real clip's layout."""
import json, re, struct
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
inp = root / "work/v20-inputs"
exe = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe").read_bytes()
rtti = sorted(set(m.group(0).decode() for m in re.finditer(rb"\.\?A[VU][A-Za-z0-9_@]*(?:Anim|Clip|Skelet|Pose|Motion|Keyframe|Spline|Compress)[A-Za-z0-9_@]*@@", exe)))
print(len(rtti)); print(rtti[:120])
print([m.group(0).decode() for m in re.finditer(rb"[ -~]{0,60}(?:\.anm|anm_bxml|anm\b|keyframe|Keyframe|spline|Spline|wavelet|delta compress|hkaAnim)[ -~]{0,60}", exe)][:50])
ref = root / "references"
for p in ref.rglob("*"):
    if p.is_file() and p.suffix in (".txt", ".md", ".cpp", ".h", ".hpp", ".py") and p.stat().st_size < 3000000:
        t = p.read_text(errors="replace")
        hits = [l.strip()[:170] for l in t.splitlines() if re.search(r"anm|anim_clip|clip|decompress|sample_pose|skeleton|keyframe|bone", l, re.I)]
        if hits:
            print("##", p.relative_to(ref), len(hits), hits[:10])
