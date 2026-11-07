import json,struct,sys,collections,hashlib
from pathlib import Path
import numpy as np
from decode_terrain_paint import parse_terrain,parse_height_chunk,entry
root=Path.home()/'Documents/Opem Amalur';out=root/'work/v43-scene-fidelity/terrain-research/proposal';b=next((root/'work/v20-inputs').rglob('431658.terrain_bin')).read_bytes();s=(root/'work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin').read_bytes();T=parse_terrain(b);keys=set(T['height']['levels'][0]['values']);A=np.full((4096,4096),255,np.uint8);C=collections.Counter();failures=[]
for key in keys:
 at=(key&0x1fffff)*64
 if struct.unpack_from('<I',s,at+4)[0]==4:continue
 _,_,d=entry(s,key,T['descriptor'])
 for g in parse_height_chunk(d):
  x0,x1,y0,y1=g['rect']
  if x1-x0!=16 or y1-y0!=16:continue
  if not g['material_sets'] or len(g['material_sets'])!=len(g['part_triangle_masks']):C['unsupported_grids']+=1;continue
  ids=g['material_sets'];assert max(ids)<7
  masks=np.stack([np.unpackbits(np.frombuffer(bytes.fromhex(q['payload_hex']),np.uint8),bitorder='little') for q in g['part_triangle_masks']]);assert masks.shape[1]==512
  owner_count=masks.sum(0);assert owner_count.max()<=1
  owner=np.full(512,7,np.uint8)
  for i,mid in enumerate(ids):owner[masks[i]!=0]=mid
  state=np.unpackbits(np.frombuffer(bytes.fromhex(g['vertex_state']['payload_hex']),np.uint8),bitorder='little')[:361].reshape(19,19)
  alt=~((state[1:17,1:17]!=0)&(state[2:18,2:18]!=0));q=owner[::2].reshape(16,16)|(owner[1::2].reshape(16,16)<<3)|(alt.astype(np.uint8)<<6)
  assert np.all(A[y0:y1,x0:x1]==255)
  A[y0:y1,x0:x1]=q;C['grids']+=1;C['unowned_triangles']+=int((owner==7).sum())
(out/'terrain-431658-selector.r8ui').write_bytes(A.tobytes());door=int(A[793,2080]);assert (door&7)==1 and ((door>>3)&7)==1
report=dict(width=4096,height=4096,format='R8UI',world_origin=[-102425,-102425],world_units_per_texel=50,scope='native terrain431658 finest-height coverage only',sentinel=255,counts=C,valid_quads=int((A!=255).sum()),empty_quads=int((A==255).sum()),door_byte=door,sha256=hashlib.sha256(A.tobytes()).hexdigest(),triangle_test_cases=[dict(diagonal='primary',fraction=[.8,.2],triangle=0),dict(diagonal='primary',fraction=[.2,.8],triangle=1),dict(diagonal='alternate',fraction=[.2,.2],triangle=0),dict(diagonal='alternate',fraction=[.8,.8],triangle=1)],shader='byte=texelFetch(selector,ivec2(floor(mapXY)),0).r; f=fract(mapXY); tri=((byte&64u)!=0u)?uint(f.x+f.y>1.):uint(f.y>f.x); materialSet=(byte>>(tri*3u))&7u;')
(out/'terrain-431658-selector.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
