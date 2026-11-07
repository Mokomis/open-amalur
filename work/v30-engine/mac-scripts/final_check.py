"""Compare final pass input and output from one frame."""
import json
from pathlib import Path
run = Path.home() / "Documents" / "Opem Amalur" / "work/v19-capture/run4"
def load(label):
    return json.loads(next(run.glob("tex_*_%s.json" % label)).read_text()), next(run.glob("tex_*_%s.raw" % label)).read_bytes()
im, a = load("final_in_in")
om, b = load("final_out")
def srgb(v):
    return 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055
raw = enc = n = 0
for y in range(120, 800, 12):
    for x in range(60, 1380, 12):
        p, q = a[y * im["pitch"] + x * 4:][:3], b[y * om["pitch"] + x * 4:][:3]
        for c in range(3):
            raw += abs(p[c] - q[c]); enc += abs(srgb(p[c] / 255) * 255 - q[c]); n += 1
print("final fmt", om["fmt"], "error if unchanged", round(raw / n, 3), "error if sRGB encoded", round(enc / n, 3))
print([(tuple(a[400 * im["pitch"] + x * 4:][:3]), tuple(b[400 * om["pitch"] + x * 4:][:3])) for x in (300, 500, 700, 900, 1100)])
