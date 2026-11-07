from pathlib import Path
import sys,struct,json,hashlib
import numpy as np
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;P=Path(r'C:\Users\rwill\Documents\Opem Amalur')
sys.path.insert(0,str(O));import audit_skinning as A
m=json.loads((O/'weights-and-palettes.json').read_text());b=(P/m['base_pack']).read_bytes();J,parents,clips,parts=A.packparts(b)
source=json.loads((P/'work/v49-character-create/vertex-contract-audit/source-join-manifest.json').read_text())
def rows(path):
 b=path.read_bytes();assert b[:8]==b'OASKPR1\0';nc,nj,npal=struct.unpack_from('<3I',b,8);a=20;out=[]
 for _ in range(nc):
  ci,fr=struct.unpack_from('<II',b,a);a+=8;q=np.frombuffer(b,'<f4',nj*4,a).reshape(nj,4).copy();a+=nj*16;t=np.frombuffer(b,'<f4',nj*3,a).reshape(nj,3).copy();a+=nj*12;r=[]
  for _ in range(npal):
   n=struct.unpack_from('<I',b,a)[0];a+=4;r.append(np.frombuffer(b,'<f4',n*12,a).reshape(n,3,4).copy());a+=n*48
  out.append((ci,fr,q,t,r))
 assert a==len(b);return out
old=rows(O/'production-pose-rows.bin');new=rows(O/'corrected-palette-pose-rows.bin');metrics=[]
def skin(p,j,w,r):
 x=np.concatenate([p,np.ones((len(p),1))],axis=1)
 applied=np.einsum('nkab,nb->nka',r[j],x)
 return (applied*w[:,:,None]).sum(1)
def stat(d):
 dist=np.linalg.norm(d,axis=1);ix=np.argsort(dist)[-3:][::-1]
 return dict(mean_cm=float(dist.mean()),p95_cm=float(np.percentile(dist,95)),max_cm=float(dist.max()),max_component_cm=float(abs(d).max()),vertices_above_1mm=int((dist>.1).sum()),top_vertices=[dict(index=int(i),distance_cm=float(dist[i]),delta_xyz_cm=d[i].tolist()) for i in ix])
for ci,fr,q,t,oldrows in old:
 current=new[ci];assert ci==current[0] and fr==current[1];assert np.array_equal(q,current[2]) and np.array_equal(t,current[3])
 for i,p in enumerate(parts[:12]):
  r=source['parts'][i];raw=(P/r['source_mesh']).read_bytes();off=r['source_vb_data_file_offset'];st=r['source_stride'];nv=p['nv']
  pos=np.ndarray((nv,3),'<f4',b,p['vertex_offset'],(52,4)).astype(float);joint=np.ndarray((nv,4),'u1',b,p['vertex_offset']+32,(52,1))
  w=np.ndarray((nv,4),'<f4',b,p['vertex_offset']+36,(52,4)).astype(float)
  sw=np.ndarray((nv,4),'<i2',raw,off+16,(st,2)).astype(float)/32767
  nw=np.column_stack([sw[:,:3],1-sw[:,:3].sum(1)])
  now=skin(pos,joint,w,oldrows[i].astype(float));corrected=skin(pos,joint,w,current[4][i].astype(float))
  if i not in [2,5]:assert np.array_equal(oldrows[i],current[4][i])
  elif i==2:assert np.array_equal(oldrows[i][1:],current[4][i][1:])
  metrics.append(dict(clip=ci,frame=fr,clip_name='idle' if ci==0 else 'walk',part=i,label=r['label'],palette_only=stat(corrected-now),
   unclamped_native_weights_same_old_matrices=stat(skin(pos,joint,nw,oldrows[i].astype(float))-now),
   incorrectly_use_all4_stored_weights=stat(skin(pos,joint,sw,oldrows[i].astype(float))-now)))
receipt=dict(result='PASS',production_cpu='Compiled current work/v19-host/oa_character.c and used actual oa_character_parse/pose/bones; same unchanged source pack for old+corrected variants; no GL/engine app.',
 production_c_sha256=A.H((P/'work/v19-host/oa_character.c').read_bytes()),production_h_sha256=A.H((P/'work/v19-host/oa_character.h').read_bytes()),
 base_pack_sha256=A.H(b),baseline_rows_sha256=A.H((O/'production-pose-rows.bin').read_bytes()),corrected_rows_sha256=A.H((O/'corrected-palette-pose-rows.bin').read_bytes()),
 cases=[dict(clip=0,frame=0,time=0),dict(clip=1,frame=8,time_policy='float32(8/fps); oa_character_pose performs existing interpolation')],
 axes='Original source xyz/cm, facing0, feet0; no camera/world/animation policy change. Both variants use identical C FK results.',
 unaffected_palettes_byte_identical=True,hip_unused_records_1_through_17_byte_identical=True,
 skin_evaluation='float64 accumulation over actual C float32 matrices and actual pack vertices/weights. Conditional position differences, not a native GPU replay; exact nativeVS instruction rounding/order not emulated.',
 metrics=metrics)
A.dump('pose-displacement-receipt.json',receipt)
for r in metrics:
 if r['part'] in [0,1,2,4,5]:print(r['clip_name'],r['part'],'paletteMax',r['palette_only']['max_cm'],'paletteMean',r['palette_only']['mean_cm'],'weightMax',r['unclamped_native_weights_same_old_matrices']['max_cm'])
