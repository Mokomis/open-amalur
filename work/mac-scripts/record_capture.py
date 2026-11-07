"""Verify the sRGB table reading over the whole cube and record the live capture findings."""
import hashlib, json
from pathlib import Path
root = Path.home() / "Documents" / "Opem Amalur"
out = root / "outputs/scene-v19"
stage = root / "work/v19-capture/run4"
tex = (root / "work/v19-inputs/initial_0.pak/1426979.dds").read_bytes()[38:]
m = json.loads(next(stage.glob("tex_*_merge_in_lut.json")).read_text())
live = next(stage.glob("tex_*_merge_in_lut.raw")).read_bytes()
def decode(v):
    v /= 255
    return (v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) * 255
results = {}
for name, order in (("b_g_r", lambda r, g, b: b * 256 + g * 16 + r), ("r_g_b", lambda r, g, b: r * 256 + g * 16 + b)):
    total = n = worst = 0
    for b in range(16):
        for g in range(16):
            for r in range(16):
                row = g * m["pitch"] + (b * 16 + r) * 4
                at = order(r, g, b) * 4
                for c in range(3):
                    e = abs(live[row + c] - decode(tex[at + c])); total += e; n += 1; worst = max(worst, e)
    results[name] = {"mean_error_levels": round(total / n, 3), "worst_levels": round(worst, 2)}
print(results)
g = (root / "work/v19-capture/run2/g_global.bin").read_bytes()
capture = {
  "scene": "Player save in Odarath, standing still, 1440x960, region key Midnight",
  "method": "Frida in-memory D3D11 observation with staging copies; no game file or config patched",
  "exe_sha256": "16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314",
  "g_global_sha256": hashlib.sha256(g).hexdigest(),
  "confirmed_live": [
    {"claim": "Region values reach g_global: sun = rgb*hdr*intensity, direction negated, fog = density/500000 and start, fog color, sky light, environment tint", "evidence": "1587639.region_bxml key Midnight matches live sun within 4.2e-6; 36 regions share these values, so the capture does not single out one region", "status": "live_confirmed"},
    {"claim": "Global scales: ambientDiffuseScale 5.0, ambientSpecularScale 0.9, backlightScale 0.12, sunlightFogTintAmount 0.5, sunlightFogTintPower 10", "evidence": "g_global offsets 1276, 1280, 1284, 1288, 1292", "status": "live_observed_one_scene"},
    {"claim": "Merge output = table(scene + 0.5376*bloom)", "evidence": "Mean error 0.313 of 255 over sampled pixels; other scales tested were worse (0: 0.995, 1: 0.876). The asm for this pass was not identified", "status": "live_measured"},
    {"claim": "Final pass does not sRGB-encode: bytes equal merge output apart from edge filtering", "evidence": "Same-frame mean error 0.096 unchanged vs 43.56 if encoded, though the texture format is R8G8B8A8_UNORM_SRGB", "status": "live_measured"},
    {"claim": "Color-correction table is sampled with sRGB decoding", "evidence": results, "status": "live_measured"},
    {"claim": "Table generator 317b351e9280c38e applies weights, pow, scale and luminance tint; all neutral in this scene (weights 0, exponent 1, scale 1)", "evidence": "Shader asm and captured 64-byte constants", "status": "live_observed_one_scene"},
    {"claim": "Lit values are not gamma-corrected before the table: combine and merge write R8G8B8A8_UNORM", "evidence": "Render target formats in frame capture", "status": "live_observed"},
    {"claim": "This frame used only the immediate context, though one deferred context is created", "evidence": "All captured events on one context", "status": "live_observed_one_scene"}],
  "v0_16_cause": "v0.16 read table 1525613 as plain RGBA8 values. If the shop table is decoded like this one, grey 136 maps near 147, not 199. Not yet tested in the shop or on the tablet",
  "not_resolved": ["Asm identity of merge and combine passes (shader pointers not mapped to hashes in the late attach)", "Shop values and table use in the actual shop", "Whether lit input levels on the tablet match the game", "Other scenes and times of day"]}
p = out / "lighting-provenance.json"
d = json.loads(p.read_text(encoding="utf-8-sig"))
d["live_capture_odarath"] = capture
p.write_text(json.dumps(d, indent=1), encoding="utf-8")
(out / "live-capture-odarath.json").write_text(json.dumps(capture, indent=1), encoding="utf-8")
note = "\nV19 LIVE CAPTURE (2026-10-31): Odarath frame captured through Frida, see outputs/scene-v19/live-capture-odarath.json and work/v19-capture/run2-run4. Decoder values confirmed live. v0.16 cause: color table is sampled with sRGB decoding, and v0.16 read raw values. Saves backup: work/v19-capture/state-before. The PC moved from 192.168.68.52 to 192.168.68.59 (same host keys). Next tablet build needs versionCode 18 or higher.\n"
for name in (out / "PROGRESS.txt", root / "work/CURRENT_STATE.txt"):
    with open(name, "a", encoding="utf-8") as f:
        f.write(note)
print("recorded")
