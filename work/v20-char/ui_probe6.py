import re, json
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
ld = root/"work/v21-ui/loc"
b = (ld/"english_loot_base_table.localization_table").read_bytes()
s = [m.decode("latin1") for m in re.findall(rb"[\x20-\x7e]{3,70}", b)]
print(len(s))
print([x for x in s if re.search(r"(?i)sword|helm|cuirass|boots|gauntlet|greaves|chakram|ring|amulet|potion|shield|buckler|faeblade", x)][:140])
all_ = json.loads((ld/"strings.json").read_text())
b2 = (ld/"english_main_table.localization_table").read_bytes()
s2 = [m.decode("latin1") for m in re.findall(rb"[\x20-\x7e]{3,50}", b2)]
want = r"(?i)^(armor rating|defense|health|mana|fate|fateshift|physical damage|elemental|piercing|bleed|poison|burn|stash|quest items|stats|skills|abilities|twists|lore|map|weapons|accessories|back|return|resume|equipped|new|sort|filter|all|gold|talk|barter|goodbye|fate meter|reckoning mode|rare|unique|set item|durability|price|value|shrines?|sagecraft|blacksmithing|alchemy|mercantile|stealth|lockpicking|detect hidden|dispelling|persuasion)$"
print(sorted({x for x in s2 if re.match(want, x)})[:80])
print([x for x in s2 if re.search(r"^[A-Z][a-z]+ [a-zA-Z' ]{3,30}$", x)][:0])
print([x for x in s2 if re.search(r"(?i)Fateless|Tirnoch|Gorhart|Agarth|Arena", x)][:12])
print([x for x in s2 if len(x)>6 and "?" in x and len(x)<48][:20])
