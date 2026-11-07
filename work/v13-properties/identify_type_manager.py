from pathlib import Path
import json,struct
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);rows=[]
for table in [0x174a6b0]:
 col=struct.unpack('<I',raw(table-4,4))[0];sig,off,cd,td,base=struct.unpack('<5I',raw(col,20));name=raw(td+8,180).split(b'\0')[0].decode('ascii');slots=struct.unpack('<12I',raw(table,48));rows.append(dict(table=hex(table),class_name=name,object_offset=off,slots=[hex(x) for x in slots]))
(r/'outputs/scene-v13/type-manager-class.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
