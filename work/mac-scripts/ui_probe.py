import json, re, collections
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
lists = {n: (root / f"outputs/{n}-archive-list.txt").read_text(errors="replace").split() for n in ("DATA", "initial", "patch")}
ext = collections.Counter()
for n, l in lists.items():
    for x in l:
        if "." in x: ext[(n, x.rsplit(".", 1)[1])] += 1
print("rare ext", sorted({e for (n, e), c in ext.items() if re.search(r"ui|font|ttf|otf|gfx|swf|fla|ntx|icon|xml|tga|png|menu", e)}))
for (n, e), c in sorted(ext.items()):
    if re.search(r"ui|font|ttf|otf|ntx|icon|png|menu", e): print(n, e, c)
for n, l in lists.items():
    u = [x for x in l if x.endswith("ui_bxml")][:40]
    if u: print(n, "ui_bxml", u)
s = json.loads((root / "work/v20-inputs/symbols.json").read_text())
print("symbols type", type(s).__name__, list(s)[:6] if isinstance(s, dict) else s[:3])
pat = re.compile(r"(?i)(^|_)(ui|hud|icon|icons|compass|minimap|reticle|crosshair|inventory|menu|font|fate|hudbar|frame|ornament|logo)(_|$)")
hits = collections.defaultdict(list)
def walk(k, v):
    if isinstance(v, dict):
        for a, b in v.items(): walk(a, b)
    elif isinstance(v, list):
        for b in v: walk(k, b)
    else:
        for t in (str(k), str(v)):
            if pat.search(t): hits[t.split("_")[0].lower()].append((k, v))
walk("", s)
print("hits", {a: len(b) for a, b in sorted(hits.items(), key=lambda kv: -len(kv[1]))[:25]})
all_ = [p for b in hits.values() for p in b]
print("sample", all_[:60])
out = {}
for a, b in hits.items():
    for k, v in b: out[str(k)] = v
(root / "work/v20-char/ui_symbols.json").write_text(json.dumps(out, indent=0))
print("wrote", len(out))
