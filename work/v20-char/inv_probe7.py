import json,re
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"
st=json.loads((root/"work/v21-ui/loc/strings.json").read_text())
want=r"(?i)^(iron|steel|azurite|sylvanite|prismere|star metal|ebony|mithril|cold iron|dwarven|health|mana|armor|value|durability|weapons?|accessories|all|equipped|consumables|reagents?|gold|healing potion|minor healing potion|greater healing potion|master healing potion|iron longsword|steel longsword|azurite longsword|hide|leather|plate|chain)$"
print(sorted({x for x in st if re.match(want,x)}))
L=(root/"work/v20-char/build_character.py").read_text().splitlines()
print("\n".join(L[80:102]));print("....");print("\n".join(L[228:256]))
print((root/"work/v20-char/character.bin").stat().st_size)
