from pathlib import Path
import struct,json,hashlib,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[3]
sys.path.insert(0,str(R/'work/v48-opening/script-audit'))
from native_name_hash import TABLE
H=lambda b:hashlib.sha256(b).hexdigest()
source=R/'work/v49-character-create/source/initial_0.pak/playercustomizationdata.bin'
b=source.read_bytes();n=struct.unpack_from('<I',b)[0]
assert n==184 and len(b)>=4+20*n
rows=[]
for i in range(n):
 w=struct.unpack_from('<5I',b,4+20*i);assert w[1]==0x20800
 rows.append(dict(row=i,file_offset=4+20*i,simtype=w[0],condition=w[1],category=w[2],race_mask=w[3],sex_mask=w[4]))
tables=[]
for p in sorted((O/'source/initial_0.pak').glob('*.conditional_expression')):
 b=p.read_bytes();version,count=struct.unpack_from('<II',b);assert version==6;at=8;entries=[]
 for i in range(count):
  start=at;ln=struct.unpack_from('<I',b,at)[0];at+=4;assert at+ln+2<=len(b)
  name=b[at:at+ln].decode('utf-8');at+=ln;size=struct.unpack_from('<H',b,at)[0];at+=2
  payload_at=at;pay=b[at:at+size];at+=size;assert len(pay)==size
  if i==2:entries.append(dict(index=i,file_offset=start,name=name,payload_offset=payload_at,payload_bytes=size,payload_hex=pay.hex()))
 assert at==len(b),(p.name,at,len(b))
 tables.append(dict(file=p.name,sha256=H(b),bytes=len(b),version=version,count=count,entry2=entries))
manifest=[]
for p in sorted((O/'source/initial_0.pak').glob('*.conditional_expression_mgr')):
 b=p.read_bytes();assert len(b)==9 and struct.unpack_from('<I',b)[0]==1
 manifest.append(dict(file=p.name,sha256=H(b),table0_key=struct.unpack_from('<I',b,4)[0],persistent_flag=b[8]))
ids=[1,2,6,7,8,9,3,4,11,10,12]
def contribution(sid,offset):
 return sum(TABLE[(offset+i)%50]*ord(c)+TABLE[ord(c)%50]*(offset+i+1)for i,c in enumerate(f'{sid:03d}'))
keys={x['table0_key']:x for x in manifest};fits=[]
for offset in range(100):
 v={sid:contribution(sid,offset)for sid in ids}
 for sid in ids:
  shift=next(iter(keys))-v[sid]
  mapping={k:keys[z+shift]['file'] for k,z in v.items()if z+shift in keys}
  if len(mapping)==len(keys)and not any(x['offset']==offset and x['remainder']==shift for x in fits):
   fits.append(dict(offset=offset,remainder=shift,mapping=mapping))
assert len(fits)==1 and fits[0]['offset']==2 and fits[0]['mapping'][1]=='persistent_table_manifest.conditional_expression_mgr'
base=next(x for x in tables if x['file']=='main_table.conditional_expression');assert base['entry2'][0]['payload_hex']=='00'
r=dict(source=str(source.relative_to(R)),source_sha256=H(source.read_bytes()),row_count=n,rows=rows,packed_condition=dict(raw=0x20800,page_id=1,table=0,entry=2),tables=tables,manifests=manifest,package_hash_fits=fits,strict_missing_link='Original archive resource key -> exact extracted main_table payload is not directly preserved by pakfileunpacker flattened duplicate filenames. Package1 manifest identity is independently constrained by all10 native-hash variations; table payload association is strong inference, not a runtime observation.',native_filter='category/race/sex masks AND condition evaluation status !=1 AND output ==1; unresolved handles returnstatus1 and are EXCLUDED')
(O/'availability-validation.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print('PASS184 identicalconditionhandles;11wholeconditiontables exactEOF;10manifesthashes oneuniquepackagefit; baseentry2literalTRUE')
