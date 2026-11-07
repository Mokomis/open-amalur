from pathlib import Path
import json,struct,csv,hashlib
r=Path.home()/'Documents/Opem Amalur';b=(r/'work/scene-inputs-v07/DATA_0.pak/524859.space_bxml').read_bytes();ptr,count=struct.unpack_from('<II',b,8+0x210);end=8+struct.unpack_from('<I',b)[0];assert ptr+count*104<=end
records=[dict(index=i,file_offset=ptr+i*104,words=list(struct.unpack_from('<26I',b,ptr+i*104)),matches=[]) for i in range(count)];wanted={v for x in records for v in x['words'] if 1<v<10000000};names={}
d=r/'references/ZucchiniZap--AmalurBxmlConverter/bin/Release/net10.0-windows/symbol_tables'
for p in d.glob('*.csv'):
 for row in csv.DictReader(p.open(encoding='utf-8-sig')):
  try:value=int(row['id'])
  except (ValueError,KeyError):continue
  if value in wanted:names.setdefault(value,[]).append((p.stem,row['value']))
for x in records:
 for i,v in enumerate(x['words']):
  for kind,name in names.get(v,[]):x['matches'].append(dict(offset=i*4,id=v,kind=kind,name=name))
o=dict(source_sha256=hashlib.sha256(b).hexdigest(),scope='Native fdc910 establishes root0x210 records stride104; record semantics pending',root_slot='0x210',pointer=ptr,count=count,stride=104,records=records)
(r/'outputs/scene-v12/actor-candidates.json').write_text(json.dumps(o,indent=2));print(json.dumps(dict(count=count,matches=[dict(index=x['index'],matches=x['matches']) for x in records]),indent=2))
