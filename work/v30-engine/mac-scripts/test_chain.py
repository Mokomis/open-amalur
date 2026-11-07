"""Test the measured post chain: does merge output equal table(scene + k*bloom), and final equal sRGB of that?"""
import json
from pathlib import Path

root = Path.home() / "Documents" / "Opem Amalur"
stage = root / "work/v19-capture/run3"


def load(label, folder=stage):
    meta = json.loads(next(folder.glob("tex_*_%s.json" % label)).read_text())
    return meta, next(folder.glob("tex_*_%s.raw" % label)).read_bytes()


smeta, scene = load("merge_in_scene")
bmeta, bloom = load("merge_in_bloom")
lmeta, lut = load("merge_in_lut")
ometa, out = load("merge_out")
fmeta, final = load("final", root / "work/v19-capture/run2")


def px(meta, data, x, y):
    at = y * meta["pitch"] + x * 4
    return data[at], data[at + 1], data[at + 2]


def table(r, g, b):
    # Trilinear lookup in 16 slices of 16x16, with blue choosing the slice.
    def fetch(i, j, k):
        at = k * 16 + i
        return lut[j * lmeta["pitch"] + at * 4:j * lmeta["pitch"] + at * 4 + 3]
    rf, gf, bf = r * 15, g * 15, b * 15
    i, j, k = min(int(rf), 14), min(int(gf), 14), min(int(bf), 14)
    a, c, e = rf - i, gf - j, bf - k
    result = []
    for ch in range(3):
        v = 0.0
        for di, wi in ((0, 1 - a), (1, a)):
            for dj, wj in ((0, 1 - c), (1, c)):
                for dk, wk in ((0, 1 - e), (1, e)):
                    v += fetch(i + di, j + dj, k + dk)[ch] * wi * wj * wk
        result.append(v)
    return result


def srgb(v):
    return 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055


def test(k, use_table=True):
    total, n = 0.0, 0
    for y in range(120, 800, 12):
        for x in range(60, 1380, 12):
            s = px(smeta, scene, x, y)
            b = px(bmeta, bloom, x // 4, y // 4)
            rgb = [min(1, (s[c] + k * b[c]) / 255) for c in range(3)]
            pred = table(*rgb) if use_table else [v * 255 for v in rgb]
            o = px(ometa, out, x, y)
            total += sum(abs(pred[c] - o[c]) for c in range(3)) / 3
            n += 1
    return total / n


print("merge_out vs scene+bloom, mean error in 8-bit levels")
print(" no table, no bloom", round(test(0, False), 3))
for k in (0, 0.25, 0.5376, 1.0, 1.0752, 2.0):
    print(" table k=%.4f" % k, round(test(k), 3))

print("final backbuffer bytes vs merge_out (backbuffer frame is from the earlier capture)")
rows = {"raw": 0.0, "srgb": 0.0}
n = 0
for y in range(120, 800, 12):
    for x in range(60, 1380, 12):
        o = px(ometa, out, x, y)
        f = px(fmeta, final, x, y)
        for c in range(3):
            rows["raw"] += abs(o[c] - f[c])
            rows["srgb"] += abs(srgb(o[c] / 255) * 255 - f[c])
        n += 3
print({k: round(v / n, 3) for k, v in rows.items()})
s = [px(ometa, out, x, 400) for x in (300, 500, 700, 900, 1100)]
print("samples merge_out", s, "final", [px(fmeta, final, x, 400) for x in (300, 500, 700, 900, 1100)])
