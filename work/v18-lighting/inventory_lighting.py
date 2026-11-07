"""Windows static lighting inventory; candidate fields stay explicitly unassigned."""
from pathlib import Path
import re,json,struct,platform,hashlib
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';o=r/'outputs/scene-v18'
s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')])
classes=[]
for m in re.finditer(rb'\.\?A[UV][ -~]{1,180}?\x00',b):
 name=m.group()[:-1].decode('ascii')
 if not any(x in name.lower()for x in ['light','environment','spacedata','space@']):continue
 td=va(m.start())-8;tables=[]
 for ref in refs(td):
  col=ref-12
  if col%4:continue
  try:words=struct.unpack('<5I',raw(col,20))
  except ValueError:continue
  if words[0]or words[1]>4096:continue
  for vref in refs(col):
   if vref%4:continue
   table=vref+4
   try:slots=struct.unpack('<32I',raw(table,128))
   except ValueError:continue
   tables.append(dict(table=hex(table),offset=words[1],slots=[hex(x)for x in slots]))
 classes.append(dict(name=name,td=hex(td),tables=tables))
(o/'lighting-rtti.json').write_text(json.dumps(classes,indent=2))
scene=(r/'work/scene-inputs-v07/DATA_0.pak/524859.space_bxml').read_bytes();assert hashlib.sha256(scene).hexdigest()=='775fb38b3fd9ff67ed3181579e935c70b33bd6831ccebf744ce4b2f6cd590143'
ptr,count=struct.unpack_from('<II',scene,8+0x90);rows=[]
for i in range(count):
 p=scene[ptr+108*i:ptr+108*(i+1)];values=struct.unpack('<27f',p);rows.append(dict(index=i,offset=ptr+108*i,raw_hex=p.hex(),candidate_position=values[:3],candidate_colors=[values[3+3*j:6+3*j]for j in range(4)],candidate_values=[values[15:19],values[19:23],values[23:27]],semantics_native_verified=False))
(o/'lighting-records-candidate.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(scene).hexdigest(),root_slot=0x90,count=count,stride=108,rows=rows),indent=2))
print(json.dumps(dict(classes=[dict(name=x['name'],tables=[t['table']for t in x['tables']])for x in classes if x['tables']],candidate_records=count),separators=(',',':')))
