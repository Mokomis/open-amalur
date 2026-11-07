from pathlib import Path
import struct,json,re
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);rows=[]
for m in re.finditer(rb'\.\?AV[^\x00]{1,240}\x00',b):
 name=m.group()[:-1].decode('ascii','replace')
 if not any(x in name for x in ['InteractionDef','InteractionMgr','PartInteraction@','.?AVInteraction@','.?AVInteractionResource@']):continue
 td=va(m.start())-8;tables=[]
 for ref in refs(td):
  col=ref-12
  try:sig,off,cd,td2,base=struct.unpack('<5I',raw(col,20))
  except ValueError:continue
  if sig or off>4096 or td2!=td:continue
  for vref in refs(col):
   if vref%4:continue
   table=vref+4;tables.append(dict(vtable=hex(table),offset=off,first_slots=[hex(x) for x in struct.unpack('<8I',raw(table,32))]))
 rows.append(dict(name=name,type_descriptor=hex(td),tables=tables))
(r/'outputs/scene-v15/interaction-rtti.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
