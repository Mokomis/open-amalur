from pathlib import Path
import struct,json
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);rows=[]
for x in [0x1758214,0x1730fbc,0x176a0d8]:rows.append(dict(address=hex(x),refs=[hex(y) for y in refs(x)]))
(r/'outputs/scene-v13/type-bundle-refs.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
