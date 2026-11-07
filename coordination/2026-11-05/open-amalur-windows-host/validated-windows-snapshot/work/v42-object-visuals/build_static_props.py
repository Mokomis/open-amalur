"""Build a bounded static visual overlay from native object placements; never modifies live assets.
Crates are reference visuals only here: no destruction, loot, AI or collision behavior recovered.
"""
from pathlib import Path
import sys,struct,json,hashlib,subprocess,math,collections
import numpy as np
from PIL import Image
w=Path(__file__).resolve().parent;r=w.parents[1];base=r/'work/v40-windows-host/assets/world';out=w/'static-props-overlay'
if out.exists():raise SystemExit('Preserve existing overlay; use a new output scope before rebuilding')
sys.path[:0]=[str(r/p)for p in ['work/v07-mesh','work/v09-textures']]
import amalur_mesh,amalur_fab,keen_texture
sha=lambda b:hashlib.sha256(b).hexdigest()
listings={}
for arch,label in [('DATA_0.pak','DATA'),('initial_0.pak','initial'),('patch_0.pak','patch')]:
 p=r/f'outputs/{label}-archive-list.txt';b=p.read_bytes();listings[arch]=set(b.decode('utf-16'if b[:2]==b'\xff\xfe'else'utf-8-sig').splitlines())
g=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning');inputs=[]
def extract(name):
 for arch in ['patch_0.pak','initial_0.pak','DATA_0.pak']:
  if name not in listings[arch]:continue
  p=r/'work/v20-inputs'/arch/name
  if not p.exists():
   p.parent.mkdir(exist_ok=True)
   result=subprocess.run([str(g/'modding/pakfileunpacker.exe'),str(g/'data'/arch),'unpack',str(p.parent),name],cwd=g/'modding',capture_output=True,timeout=60)
   if result.returncode or not p.exists():raise RuntimeError('Extraction failed: '+name)
  inputs.append({'path':str(p),'sha256':sha(p.read_bytes())});return p
 raise FileNotFoundError(name)
cat=json.loads((w/'direct-rendering-catalog.json').read_text());placements=[x for x in cat['instances']if x['type_name'] in ({f'smashable_crate_{i:02d}' for i in range(1,7)}|{'smashable_barrel_01','smashable_urn_01','smashable_urn_02'})]
assert placements and all(len(x['rendering'])==1 for x in placements)
models={};model_materials={};material_slots={};identity=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
for fid in sorted({x['rendering'][0]['primary_fab']for x in placements}):
 fb=extract(f'{fid}.fab_bxml');vis=extract(f'{fid}.fab_visual_data_streamable_bin');f=amalur_fab.parse_file(fb);m=amalur_mesh.parse_file(vis)
 assert f['status']=='parsed-reference-profile' and f['mesh_count']==len(m['assemblies'])==1
 desc=f['mesh_descriptors'][0];assert not desc['remaps'] and all(abs(a-b)<1e-6 for a,b in zip(desc['static_bind_candidate'],identity))
 mid=struct.unpack('<I',bytes.fromhex(desc['tail25_hex'])[:4])[0];assert mid in {301326,299790,1377236}
 model_materials[fid]=mid;models[fid]=(vis,m)
for mid in sorted(set(model_materials.values())):
 mat=extract(f'{mid}.mat_bxml').read_bytes();pp,pc,tp,tc,shader=struct.unpack_from('<5I',mat,8)
 assert tp==pp+pc*24 and tp+tc*8==8+struct.unpack_from('<I',mat)[0]
 slots={slot:tid for tid,slot in [struct.unpack_from('<II',mat,tp+i*8)for i in range(tc)]}
 assert shader==8827 and len(slots)==tc==4 and slots[1]==250070 and set(slots)=={0,1,2,3}
 material_slots[mid]=slots
original_materials=(base/'materials.bin').read_bytes();nm=struct.unpack_from('<I',original_materials)[0];assert len(original_materials)==4+nm*28
old_materials=[struct.unpack_from('<7I',original_materials,4+i*28)for i in range(nm)]
texture_count=max(t for mat in old_materials for t in mat[1:]if t!=0xffffffff)+1
out.mkdir();files={}
def save(name,data):
 (out/name).write_bytes(data);files[name]={'sha256':sha(data),'bytes':len(data),'before_sha256':sha((base/name).read_bytes())if(base/name).exists()else None}
def stored_mips(raw):
 # Stream carriers may end above 4x4. Respect declared mip count and require
 # exact byte consumption, rather than inventing absent small levels.
 assert 38<=len(raw)<=keen_texture.MAX_FILE_BYTES and raw[16:20]==b'KEEN'
 tid,ow,oh=struct.unpack_from('<IHH',raw);shift,unknown=struct.unpack_from('<II',raw,8);tw,th=struct.unpack_from('<HH',raw,20)
 fmt=raw[29];count=struct.unpack_from('<H',raw,35)[0]
 assert unknown==0 and fmt in (1,5) and 1<=count<=13
 assert raw[24:29]==bytes([1,0,1,0,1]) and raw[30:35]==bytes(5) and raw[37]==1
 assert all(4<=d<=4096 and d&(d-1)==0 for d in [ow,oh,tw,th]) and shift<=10 and ow>>shift==tw and oh>>shift==th
 at=38;levels=[];lw,lh=tw,th
 for level in range(count):
  size=((lw+3)//4)*((lh+3)//4)*(8 if fmt==1 else 16);assert at+size<=len(raw)
  levels.append({'width':lw,'height':lh,'offset':at,'bytes':size});at+=size;lw,lh=max(1,lw//2),max(1,lh//2)
 assert at==len(raw)
 return {'asset_id':tid,'observed_format':fmt,'mips':levels,'source_sha256':sha(raw)}
texture_ids=[];new_materials=[];material_index={}
for mid,slot in [(mid,slot)for mid in sorted(material_slots)for slot in [0,3,2]]:
 slots=material_slots[mid];tid=slots[slot];candidates=[]
 for name in [f'{tid}.dds']+[f'{tid}_{k}.dds'for k in range(6)]:
  try:p=extract(name)
  except FileNotFoundError:continue
  raw=p.read_bytes();info=stored_mips(raw)
  for level,l in enumerate(info['mips']):
   if max(l['width'],l['height'])<=1024:candidates.append((l['width']*l['height'],raw,level,p));break
 if not candidates:raise RuntimeError('No admitted texture for '+str(tid))
 _,raw,level,p=max(candidates,key=lambda x:x[0]);info=stored_mips(raw);mip=info['mips'][level];assert info['asset_id']==tid
 rgba=keen_texture.decode_blocks(raw[mip['offset']:mip['offset']+mip['bytes']],mip['width'],mip['height'],info['observed_format'])
 receipt={'decoded_width':mip['width'],'decoded_height':mip['height']}
 image=Image.frombytes('RGBA',(receipt['decoded_width'],receipt['decoded_height']),rgba);levels=[]
 while True:
  levels.append(image.tobytes())
  if image.width==image.height==1:break
  image=image.resize((max(1,image.width//2),max(1,image.height//2)),Image.Resampling.BOX)
 data=b'OATX'+struct.pack('<4I',0x8058,receipt['decoded_width'],receipt['decoded_height'],len(levels))+b''.join(struct.pack('<I',len(x))+x for x in levels)
 idx=texture_count+len(texture_ids);texture_ids.append(idx);save(f't{idx}.bin',data)
for i,mid in enumerate(sorted(material_slots)):
 material_index[mid]=nm+i
 new_materials.append(struct.pack('<7I',128<<8,*texture_ids[i*3:i*3+3],0xffffffff,0xffffffff,0xffffffff))
save('materials.bin',struct.pack('<I',nm+len(new_materials))+original_materials[4:]+b''.join(new_materials))
water=(base/'water.bin').read_bytes();assert len(water)==4+nm*44;save('water.bin',struct.pack('<I',nm+len(new_materials))+water[4:]+bytes(44*len(new_materials)))
index=bytearray((base/'index.bin').read_bytes());cellsize,nc=struct.unpack_from('<fI',index,4);assert len(index)==20+nc*48
dtype=np.dtype([('p','<f4',3),('n','<i2',4),('uv','<f4',2)]);assert dtype.itemsize==28
model_arrays={}
for fid,(vis,m)in models.items():
 asm=m['assemblies'][0];vb=m['vertex_buffers'][asm['vertex_buffer']];ib=np.array(m['index_buffers'][asm['index_buffer']]['indices'],dtype='<u4');assert vb['stride_bytes']==48 and asm['unknown_u16_at2']==0
 raw=vis.read_bytes();P=np.array(vb['positions'],dtype=np.float64);N=np.ndarray((len(P),3),'<i2',raw,vb['data_file_offset']+20,(48,2)).astype(np.float64)/32767;UV=np.ndarray((len(P),2),'<f4',raw,vb['data_file_offset']+12,(48,4)).copy()
 model_arrays[fid]=(P,N,UV,ib)
buckets=collections.defaultdict(list);receipt=[]
def qrot(q,v):
 u=np.array(q[:3]);t=2*np.cross(u,v);return v+q[3]*t+np.cross(u,t)
for obj in placements:
 fid=obj['rendering'][0]['primary_fab'];P,N,UV,ib=model_arrays[fid]
 assert all(abs(s-1)<1e-6 for s in obj['scale'])
 q=obj['quaternion'];q=[-q[0],-q[1],-q[2],q[3]];wp=qrot(q,P)+obj['position'];wn=qrot(q,N);wn/=np.linalg.norm(wn,axis=1,keepdims=True)
 verts=np.zeros(len(P),dtype=dtype);verts['p']=wp;verts['n'][:,:3]=np.round(wn*32767).astype('<i2');verts['n'][:,3]=32767;verts['uv']=UV
 key=tuple(math.floor(p/cellsize)for p in obj['position'][:2]);buckets[key].append((verts,ib,material_index[model_materials[fid]]));receipt.append({'instance_id':obj['instance_id'],'type_id':obj['type_id'],'fab_id':fid,'triangles':len(ib)//3,'position':obj['position'],'quaternion':obj['quaternion'],'cell':key,'bounds':[wp.min(0).tolist(),wp.max(0).tolist()]})
for key,parts in buckets.items():
 matches=[i for i in range(nc)if struct.unpack_from('<ii',index,20+i*48)==key];assert len(matches)==1;row=20+matches[0]*48
 parts=sorted(parts,key=lambda x:x[2]);new_v=np.concatenate([v for v,i,mi in parts]);all_i=[];off=0;new_draws=[];first=0
 for material in sorted({mi for v,i,mi in parts}):
  n=0
  for verts,indices,mi in parts:
   if mi!=material:continue
   all_i.append(indices+off);off+=len(verts);n+=len(indices)
  new_draws.append((material,first,n));first+=n
 new_i=np.concatenate(all_i)
 for lod in range(3):
  name=f'c{key[0]}_{key[1]}_{lod}.bin';b=(base/name).read_bytes();assert b[:4]==b'OAWC';nv,ni,nd=struct.unpack_from('<3I',b,4);assert nd+len(new_draws)<=128 and len(b)==16+nd*12+nv*28+ni*4
  olddraw=b[16:16+nd*12];oldv=b[16+nd*12:16+nd*12+nv*28];oldi=b[16+nd*12+nv*28:]
  result=b'OAWC'+struct.pack('<3I',nv+len(new_v),ni+len(new_i),nd+len(new_draws))+olddraw+b''.join(struct.pack('<3I',mi,ni+first,n)for mi,first,n in new_draws)+oldv+new_v.tobytes()+oldi+(new_i+nv).astype('<u4').tobytes();save(name,result)
  struct.pack_into('<I',index,row+32+lod*4,(ni+len(new_i))//3)
 lo=np.minimum(np.array(struct.unpack_from('<3f',index,row+8)),new_v['p'].min(0));hi=np.maximum(np.array(struct.unpack_from('<3f',index,row+20)),new_v['p'].max(0));struct.pack_into('<6f',index,row+8,*lo,*hi)
save('index.bin',bytes(index))
manifest={'type_ids':sorted({x['type_id']for x in placements}),'fab_ids':sorted(models),'material_ids':sorted(material_slots),'native_rendering_reference_evidence':'00f0cc50 +0x14; previously established Workbench FAB field','placements':receipt,'files':files,'inputs':inputs,'added_triangles_lod0':sum(x['triangles']for x in receipt),'limits':['Static visual recovery only; native destruction/loot/collision behavior not implemented','Material uses the current custom shader approximations; texture roles 0 diffuse/3 normal/2 specular corroborated by texture symbols, not original shader parity','Identity FAB bind and unit placement scale only; no general skeletal assumptions','All three existing stream LODs retain this small mesh unchanged']}
(w/'static-props-manifest.json').write_text(json.dumps(manifest,indent=2));print('Built',len(placements),'static prop visuals in',len(buckets),'cells;',len(files),'files;',manifest['added_triangles_lod0'],'triangles')
