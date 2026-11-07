from pathlib import Path
import re,json,struct
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);rows=[]
for m in re.finditer(rb'\.\?A[UV][ -~]{1,800}?\x00',b):
 name=m.group()[:-1].decode('ascii')
 if 'AssetCategoryMgrProxy@$0CP@' not in name:continue
 addr=va(m.start());tables=[]
 for ref in refs(addr-8):
  col=ref-12
  try:d=struct.unpack('<5I',raw(col,20))
  except ValueError:continue
  if d[0] or d[1]>4096:continue
  for vref in refs(col):
   if vref%4:continue
   try:slots=struct.unpack('<20I',raw(vref+4,80))
   except ValueError:continue
   tables.append(dict(table=hex(vref+4),slots=[hex(x) for x in slots]))
 rows.append(dict(name=name,tables=tables))
(r/'outputs/scene-v13/simtype-proxy.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
