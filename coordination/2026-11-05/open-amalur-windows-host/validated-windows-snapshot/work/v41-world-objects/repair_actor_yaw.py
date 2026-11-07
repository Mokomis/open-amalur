"""Repair placed actors' GOR quaternion read; preserve original models and encounter poses.
Uses native quaternion fields and the previously verified conjugated world-matrix
convention. Host AI, animation policy and planar-only actor heading remain authored.
"""
from pathlib import Path
import struct,json,math,collections,argparse,hashlib,shutil
w=Path(__file__).resolve().parent;r=w.parents[1]
import sys
sys.path.insert(0,str(r/'work/v20-char'))
from native_instances import heading_xy
p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');a=p.parse_args()
if a.apply:
 proof=json.loads((w/'native-heading-validation.json').read_text())
 if proof.get('tested',0)<1 or proof.get('max_radians_error',float('inf'))>=1e-5:
  raise SystemExit('Native heading validation is required before applying placement changes')
catalog=json.loads((w/'native-placement-catalog.json').read_text());spaces={v['space_id'] for v in catalog['spaces']}
records=collections.defaultdict(list)
for row in catalog['global_records']:
 if row['space_id'] in spaces and row['type_name']:
  records[(row['type_name'],struct.pack('<3f',*row['position']))].append(row)
types=json.loads((r/'work/v23-actors/report.json').read_text())['types'];results=[]
for label,path in [('source',r/'work/v23-actors/index.bin'),('desktop',r/'work/v40-windows-host/assets/actors/index.bin')]:
 data=path.read_bytes();out=bytearray(data);magic,n_types,n_actors=struct.unpack_from('<4sII',data);assert magic==b'OAAI' and n_types==len(types)
 base=12+n_types*76;assert len(data)==base+n_actors*20
 changes=[];unmatched=[];placed=0
 for i in range(n_actors):
  at=base+i*20;x,y,z,old,ti,group=struct.unpack_from('<4fHH',data,at)
  if group:continue
  placed+=1;key=(types[ti]['sim'],data[at:at+12]);rows=records.get(key,[])
  if len(rows)!=1:unmatched.append({'index':i,'type':types[ti]['sim'],'position':[x,y,z],'matches':len(rows)});continue
  row=rows[0];q=row['quaternion'];new=heading_xy(q)
  if abs(math.remainder(new-old,math.tau))<1e-6:continue
  struct.pack_into('<f',out,at+12,new)
  changes.append({'index':i,'type':types[ti]['sim'],'instance_id':row['instance_id'],'source':row['source'],'old_yaw':old,'new_yaw':new,'raw_native_quaternion':q})
 result={'target':label,'path':str(path),'placed':placed,'changed':len(changes),'unmatched':unmatched,'changes':changes,'before_sha256':hashlib.sha256(data).hexdigest(),'after_sha256':hashlib.sha256(out).hexdigest(),'applied':a.apply}
 results.append(result)
 if a.apply and changes:
  backup=w/'before'/('index-'+label+'.bin');backup.parent.mkdir(exist_ok=True)
  if backup.exists():assert backup.read_bytes()==data,'Preserve earlier repair evidence; review before repeating'
  else:backup.write_bytes(data)
  path.write_bytes(out)
 print(label,'placed',placed,'yaw fixes',len(changes),'unmatched',len(unmatched))
report=w/('yaw-repair-applied.json' if a.apply else 'yaw-repair-preview.json')
if not report.exists():report.write_text(json.dumps(results,indent=2))
else:print('Existing report preserved:',report)
