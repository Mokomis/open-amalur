from pathlib import Path
import hashlib,json,struct
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');V=P/'work/v45-foliage-coverage';W=P/'work/v40-windows-host/assets/world';OUT=V/'final-material-placement-stage';S=OUT/'world';S.mkdir(parents=True,exist_ok=True);C=V/'image-band-audit/left-bridge-structure/cart-material';L=V/'native-leaf-direct-trs';M={'status':'staged only','overrides':{},'new_files':{},'leaf_source_records':[457,458,467,468,484],'leaf_unproven73_preserved':True};sha=lambda b:hashlib.sha256(b).hexdigest()
def put(name,b):
 (S/name).write_bytes(b);r={'bytes':len(b),'sha256':sha(b)}
 if (W/name).exists():r['before_sha256']=sha((W/name).read_bytes());M['overrides'][name]=r
 else:M['new_files'][name]=r
b=(W/'materials.bin').read_bytes();assert struct.unpack_from('<I',b)[0]==299;row=(C/'material-row299.bin').read_bytes();assert len(row)==28;put('materials.bin',struct.pack('<I',300)+b[4:]+row)
b=(W/'native-materials.bin').read_bytes();assert struct.unpack_from('<I',b,8)[0]==299;row=(C/'native-material-row299.bin').read_bytes();assert len(row)==84;put('native-materials.bin',b[:8]+struct.pack('<I',300)+b[12:]+row)
for f in sorted((C/'world').glob('t*.bin')):put(f.name,f.read_bytes())
put('cart-environment.bin',(C/'cart-environment.bin').read_bytes())
changed=[]
for f in sorted((L/'proven-world').glob('l*.bin')):
 if f.name=='leaf-index.bin':continue
 data=f.read_bytes();assert (W/f.name).read_bytes()==(L/'input-world'/f.name).read_bytes(),f.name
 if data!=(W/f.name).read_bytes():put(f.name,data);changed.append(f.name)
assert len(changed)==6,changed
b=bytearray((L/'proven-world/leaf-index.bin').read_bytes());assert struct.unpack_from('<I',b,16)[0]==299;struct.pack_into('<I',b,16,300);put('leaf-index.bin',b)
name='r0_-14.bin';b=bytearray((W/name).read_bytes());assert b[:8]==b'OARGEO1\0';nr=struct.unpack_from('<I',b,16)[0];hits=0
for j in range(nr):
 off=28+j*48;r=struct.unpack_from('<4I6fIf',b,off)
 if r[10]==0x50000000+1390820:
  assert r[0]==10 and r[2]==3888;struct.pack_into('<I',b,off,299);hits+=1
assert hits==1;put(name,b)
b=bytearray((W/'region-index.bin').read_bytes());assert struct.unpack_from('<I',b,12)[0]==299;struct.pack_into('<I',b,12,300);n=struct.unpack_from('<I',b,8)[0];bound_only=[]
for r in json.loads((L/'proven-only-bounds-expansion.json').read_text()):
 found=False
 for j in range(n):
  off=24+j*40
  if struct.unpack_from('<2i',b,off)==tuple(r['cell']):
   old=struct.unpack_from('<6f',b,off+16);bounds=r['required_union_bounds'];new=[min(old[k],bounds[0][k]) for k in range(3)]+[max(old[k+3],bounds[1][k]) for k in range(3)];struct.pack_into('<6f',b,off+16,*new);found=True;break
 if not found:
  bounds=r['required_union_bounds'];b+=struct.pack('<iiII6f',*r['cell'],0,0,*bounds[0],*bounds[1]);n+=1;struct.pack_into('<I',b,8,n);bound_only.append(r['cell'])
put('region-index.bin',b);M.update(changed_leaf_cells=changed,cart_source_range_alias_changes=hits,material_count=300,metadata_only_bound_cells=bound_only);(OUT/'manifest.json').write_text(json.dumps(M,indent=2));print(json.dumps({k:x for k,x in M.items() if k not in ['overrides','new_files']},indent=2))
