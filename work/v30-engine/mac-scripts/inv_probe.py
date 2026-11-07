import json, re, collections
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
s = json.loads((root / "work/v20-inputs/symbols.json").read_text())
sim = s["simtype"]
print("simtype", len(sim))
names = {k: str(v) for k, v in sim.items()}
for pat in [r"(?i)longsword", r"(?i)^(wpn|weapon|item)", r"(?i)sword", r"(?i)cuirass|chest|torso", r"(?i)potion", r"(?i)reagent"]:
    hit = [f"{k}:{n}" for k, n in names.items() if re.search(pat, n)]
    print("==", pat, len(hit), hit[:22])
pref = collections.Counter(n.split("_")[0].lower() for n in names.values())
print("prefix", pref.most_common(40))
print("fab 1327249", s["fab"].get("1327249"))
ref = root / "references"
print([p.name for p in ref.iterdir()])
conv = ref / "ZucchiniZap--AmalurBxmlConverter"
print([p.relative_to(conv).as_posix() for p in conv.rglob("*") if p.is_file() and ".git" not in p.parts][:40])
print("patterns", [p.name for p in (root/"outputs").glob("*simtype*")][:5])
L = (root/"outputs/initial-archive-list.txt").read_text(errors="replace").split()
print("simtype files", [x for x in L if "simtype" in x][:8], sum("simtype" in x for x in L))
for key in ("loottable",): print(key, list(s[key].items())[:6])
