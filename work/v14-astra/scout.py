from pathlib import Path
import struct,json,re,hashlib
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);out=r/'outputs/scene-v14-astra';rows=[]
for m in re.finditer(rb'\.\?A[UV][^\x00]{1,500}',b):
 name=m.group().decode('ascii','replace')
 if not any(t in name for t in ['StreamableDecompressor','SegmentedDecompressor']):continue
 addr=va(m.start());tables=[]
 for ref in refs(addr-8):
  col=ref-12
  try:d=struct.unpack('<5I',raw(col,20))
  except ValueError:continue
  if d[0] or d[1]>4096:continue
  for vref in refs(col):
   if vref%4:continue
   try:slots=struct.unpack('<12I',raw(vref+4,48))
   except ValueError:continue
   tables.append(dict(vtable=hex(vref+4),offset=d[1],slots=[hex(x) for x in slots]))
 rows.append(dict(name=name,tables=tables))
strings=[]
for token in [b'simtype',b'SimType',b'partset',b'PartSet']:
 for m in re.finditer(re.escape(token),b):
  a=va(m.start());strings.append(dict(text=b[m.start():m.start()+150].split(b'\0')[0].decode('ascii','replace'),va=hex(a),refs=[hex(x) for x in refs(a)]))
result=dict(sha256=hashlib.sha256(b).hexdigest(),rtti=rows,strings=strings)
(out/'upstream-scout.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
