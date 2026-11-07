"""Bounded on-disk evidence; address matches are candidates until decoded."""
from pathlib import Path
import re,json,struct,hashlib
r=Path.home()/'Documents/Opem Amalur'
s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')])
rows=[]
for m in re.finditer(rb'\.\?A[UV][ -~]{1,180}?\x00',b):
 name=m.group()[:-1].decode('ascii')
 if not any(x.lower() in name.lower() for x in ['SimType@BHG','SimTypeDef']):continue
 addr=va(m.start());tables=[]
 if not addr:continue
 for ref in refs(addr-8):
  col=ref-12
  try:d=struct.unpack('<5I',raw(col,20))
  except ValueError:continue
  if d[0] or d[1]>4096:continue
  for vref in refs(col):
   if vref%4:continue
   try:slots=struct.unpack('<20I',raw(vref+4,80))
   except ValueError:continue
   tables.append(dict(vtable=hex(vref+4),offset=d[1],slots=[hex(x) for x in slots]))
 rows.append(dict(name=name,tables=tables))
calls=[]
for target in [0x1071570,0x1194e70]:
 hits=[]
 for a,n,o in secs:
  data=b[o:o+n];at=data.find(b'\xe8')
  while at>=0:
   if at+5<=n and (a+at+5+struct.unpack_from('<i',data,at+1)[0])&0xffffffff==target:hits.append(hex(a+at))
   at=data.find(b'\xe8',at+1)
 calls.append(dict(target=hex(target),candidate_calls=hits))
strings=[]
for token in [b'Duplicate vertex format attribute',b'COLLISION_SET',b'CollisionSet']:
 items=[]
 for m in re.finditer(re.escape(token),b):
  a=va(m.start())
  if a:items.append(dict(address=hex(a),refs=[hex(x) for x in refs(a)]))
 strings.append(dict(token=token.decode(),items=items[:40]))
x=dict(target_sha256=hashlib.sha256(b).hexdigest(),rtti=rows,calls=calls,strings=strings)
(r/'outputs/scene-v12/simtype-native-candidates.json').write_text(json.dumps(x,indent=2));print(json.dumps(x,indent=2))
