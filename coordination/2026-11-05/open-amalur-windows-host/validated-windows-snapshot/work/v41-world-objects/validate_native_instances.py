from pathlib import Path
import sys,json,collections,math,struct,hashlib
r=Path(__file__).resolve().parents[1].parent
sys.path.insert(0,str(r/'work/v20-char'))
from native_instances import parse_space,parse_gor,PlacementError
syms=json.loads((r/'work/v20-inputs/symbols.json').read_text())
listings={}
for arch,label in [('DATA_0.pak','DATA'),('initial_0.pak','initial'),('patch_0.pak','patch')]:
 b=(r/f'outputs/{label}-archive-list.txt').read_bytes();listings[arch]=set(b.decode('utf-16' if b[:2]==b'\xff\xfe' else 'utf-8-sig').splitlines())
def latest(name):
 for arch in ['patch_0.pak','initial_0.pak','DATA_0.pak']:
  if name in listings[arch]:
   p=r/'work/v20-inputs'/arch/name
   if not p.exists():raise RuntimeError('Latest archive member has not been extracted: '+str(p))
   return p
 raise FileNotFoundError(name)
records=[];spaces=[];global_records=[];by_key={};stats=collections.Counter();differences=[]
for sid,name in syms['simspace'].items():
 if not name.startswith('out_dal_'):continue
 p=latest(f'{sid}.space_bxml');b=p.read_bytes();obj=parse_space(b)
 assert obj['space_id']==int(sid)
 spaces.append({'space_id':int(sid),'name':name,'source':str(p),'sha256':hashlib.sha256(b).hexdigest(),'count':obj['count']})
 for i,x in enumerate(obj['records']):
  x.update(space_id=int(sid),space_name=name,index=i,type_name=syms['simtype'].get(str(x['type_id'])))
  key=(int(sid),x['instance_id']);stats['duplicate_instance_keys']+=key in by_key;by_key[key]=x;records.append(x)
  stats['space_records']+=1;stats['unit_quaternions']+=abs(sum(q*q for q in x['quaternion'])-1)<.002;stats['types_below_2']+=x['type_id']<2;stats['named_types']+=x['type_name'] is not None
for name in sorted(listings['initial_0.pak']):
 if not name.endswith('.gor_bxml'):continue
 p=latest(name);g=parse_gor(p.read_bytes());x=g['record'];key=(g['space_id'],x['instance_id'])
 stats['gor_records']+=1;stats['gor_header_word_1']+=g['header_word_12']==1
 stats['gor_unit_quaternions']+=abs(sum(q*q for q in x['quaternion'])-1)<.002
 stats['gor_named_types']+=str(x['type_id']) in syms['simtype']
 oldq=struct.unpack_from('<4f',p.read_bytes(),36)
 stats['legacy_gor_quaternion_not_unit']+=abs(sum(q*q for q in oldq)-1)>=.002
 x.update(space_id=g['space_id'],type_name=syms['simtype'].get(str(x['type_id'])),source=str(p),header_word_12=g['header_word_12'])
 global_records.append(x)
 if key in by_key:
  stats['paired_space_gor']+=1;y=by_key[key]
  fields=['position','quaternion','scale','type_id','flags','name']
  bad={f:[y[f],x[f]] for f in fields if y[f]!=x[f]}
  if bad:differences.append({'key':key,'file':str(p),'fields':bad})
  else:stats['paired_exact_named_fields']+=1
# Reject impossible spans before iterating. This exercises a hostile count in real data.
b=bytearray(latest('431638.space_bxml').read_bytes());struct.pack_into('<II',b,8+0x210,0xfffffff0,0x100000)
try:parse_space(b)
except PlacementError:stats['invalid_array_rejected']+=1
else:raise AssertionError('Invalid placement array accepted')
output=Path(__file__).resolve().parent
(output/'native-placement-catalog.json').write_text(json.dumps({'evidence':['00fdc910','00fe4970','00f92480','00f92080','00f873a0','00f72340'],'stats':dict(stats),'spaces':spaces,'records':records,'global_records':global_records,'space_gor_differences':differences},indent=2))
print(json.dumps(dict(stats),indent=2));print('Independent GOR/space differences',len(differences));print(json.dumps(differences[:3],indent=2))
