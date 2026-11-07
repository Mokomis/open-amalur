from pathlib import Path
import json,struct
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);rows=[]
for token in [b'on_interact\0',b'OnInteract\0',b'on_creation\0']:
 start=0
 while (pos:=b.find(token,start))>=0:
  addr=va(pos)
  if addr:rows.append(dict(token=token[:-1].decode('ascii'),address=hex(addr),refs=[hex(x) for x in refs(addr)]))
  start=pos+1
(r/'outputs/scene-v15/interaction-dispatch-strings.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
