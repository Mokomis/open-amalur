import sys,struct,json,re,hashlib
from pathlib import Path
r=Path.home()/'Documents/Opem Amalur';sys.path.insert(0,str(r/'work/v07-bxml'));from amalur_blob import parse_bytes
rows=[]
for archive in ['DATA_0.pak','patch_0.pak']:
 p=r/'work/scene-inputs-v09'/archive/'524858.collision_set_bin';b=p.read_bytes();blob=parse_bytes(b)
 rows.append(dict(archive=archive,sha256=hashlib.sha256(b).hexdigest(),header=blob['header'],slots=blob['slots'],root_words=[dict(offset=i,u32=struct.unpack_from('<I',b,i+8)[0],f32=repr(struct.unpack_from('<f',b,i+8)[0])) for i in range(0,88,4)],strings=[dict(offset=m.start(),text=m.group().decode('ascii')) for m in list(re.finditer(rb'[ -~]{8,}',b))[:25]]))
p=r/'outputs/scene-v10/collision-carrier.json';p.write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2)[:14000])
