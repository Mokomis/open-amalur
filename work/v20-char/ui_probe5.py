import re, subprocess, json
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
ld = root/"work/v21-ui/loc"; ld.mkdir(parents=True, exist_ok=True)
L = (root/"outputs/initial-archive-list.txt").read_text(errors="replace").split()
loc = [x for x in L if x.startswith("english") and x.endswith(".localization_table")]
print("english tables", len(loc), loc[:5])
for i in range(0, len(loc), 60):
    subprocess.run([str(g/"modding/pakfileunpacker.exe"), str(g/"data/initial_0.pak"), "unpack", str(ld), *loc[i:i+60]], cwd=g/"modding", capture_output=True, timeout=300)
fs = sorted(ld.glob("*.localization_table"), key=lambda p: -p.stat().st_size)
print("got", len(fs), [(f.name, f.stat().st_size) for f in fs[:6]], fs[0].read_bytes()[:64].hex())
all_ = set()
for f in fs:
    b = f.read_bytes()
    for m in re.findall(rb"(?:[\x20-\x7e\x92\x27]\x00){3,160}", b):
        all_.add(m.decode("utf-16le", "replace"))
    if len(all_) < 50:
        for m in re.findall(rb"[\x20-\x7e]{3,160}", b): all_.add(m.decode())
print("strings", len(all_))
(ld/"strings.json").write_text(json.dumps(sorted(all_)))
def show(p, n=30, mx=40):
    r = sorted({s for s in all_ if re.fullmatch(p, s) and len(s) <= mx})
    print("==", p, len(r), r[:n])
for p in [r".*Longsword", r".*Great ?sword", r".*Chakrams?", r".*Faeblades?", r".*Daggers?", r".*Sceptre", r".*Staff", r".*(Helm|Helmet|Hood|Cuirass|Chestpiece|Leggings|Boots|Gauntlets|Greaves)", r".*Ring", r".*Potion.*", r"(Inventory|Quests?|Abilities|Destinies|Destiny|Map|World Map|Lore|Options|Settings|Save Game|Load Game|Continue|Resume|Quit|Exit|New Game|Weapons|Armor|Accessories|Consumables|Reagents|Components|Gems?|Junk|Quest Items|Twists|Fate|Fateshift|Reckoning|Reckoning Mode|Gold|Level|Experience|Health|Mana|Armor Rating|Damage|Durability|Rarity|Weight|Value|Equip|Unequip|Drop|Compare|Sort|Stash|Merchant|Buy|Sell|Repair|Save|Might|Finesse|Sorcery)"]:
    show(p, 40)
show(r".*(Dalentarth|Gorhart).*", 12, 60)
show(r".*(Sir |Alyn|Agarth|Hugues|Fomorous).*", 8, 40)
