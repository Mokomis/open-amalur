from pathlib import Path
import struct,json,sys
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);rows=[]
for arg in sys.argv[1:]:
 table=int(arg,0);items=struct.unpack('<24I',raw(table,96));rows.append(dict(table=arg,slots={hex(i*4):hex(x) for i,x in enumerate(items)}))
(r/'outputs/scene-v13/request-tables.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
