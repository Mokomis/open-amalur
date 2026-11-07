from pathlib import Path
import json,struct
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);table=0x174d554
rows=[dict(offset=hex(i),address=hex(struct.unpack('<I',raw(table+i,4))[0]),consumer_proven=i in [0xb8,0xcc]) for i in range(0xb0,0xe0,4)]
(r/'outputs/scene-v15/manager-tail-slots.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
