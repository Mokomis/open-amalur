"""Add native collection SPACE ownership to existing leaves; isolated candidate only.
Dense mode retains exact vertices and index ordering. No distance cutoff or pose edits.
"""
from pathlib import Path
import hashlib,json,struct,collections
import numpy as np
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent
A=P/'work/v45-foliage-coverage';W=P/'work/v40-windows-host/assets/world';O=Q/'candidate-world';O.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
source=json.loads((A/'expanded-leaf-attributes/source-provenance.json').read_text())
ownership={f['file']:f for f in json.loads((A/'native-leaf-direct-trs/manifest.json').read_text())['files']}
source_owner=np.concatenate([np.full(s['triangles'],i,int) for i,s in enumerate(source)])
assert len(source_owner)==51831 and len(source)==590
li=(W/'leaf-index.bin').read_bytes();assert li[:8]==b'OALF001\0'
nc,nmaps,mc=struct.unpack_from('<3I',li,8);assert nc==175 and mc==301
files=[];space_counts=collections.Counter();seen=collections.Counter()
for row in range(nc):
 cx,cy,nt=struct.unpack_from('<iiI',li,20+nmaps*8+row*12);fn=f'l{cx}_{cy}.bin';b=(W/fn).read_bytes()
 assert b==(A/'native-leaf-direct-trs/proven-world'/fn).read_bytes()
 magic,nv,ni,nd=struct.unpack_from('<4s3I',b);assert magic==b'OAWE' and nt==ni//3
 at=16+12*nd;verts=b[at:at+76*nv];indices=b[at+76*nv:];assert len(indices)==ni*4
 ot=ownership[fn]['source_triangles'];assert len(ot)==nt
 ids=source_owner[np.asarray(ot)];spaces=np.asarray([source[int(i)]['space'] for i in ids],dtype='<u4')
 mats=np.empty(nt,'<u4')
 for j in range(nd):
  mat,first,count=struct.unpack_from('<3I',b,16+12*j);mats[first//3:(first+count)//3]=mat
 ranges=[];start=0
 while start<nt:
  end=start+1
  while end<nt and mats[end]==mats[start] and spaces[end]==spaces[start]:end+=1
  # Reserved range flag marks source as native collection Space assetID.
  # Global Region ranges remain separate and unchanged. Unbounded ranges
  # preserve prior triangle selection; native Space admission is independent.
  ranges.append(struct.pack('<4I6fIf',int(mats[start]),3*start,3*(end-start),0x40000000,0,0,0,0,0,np.finfo(np.float32).max,int(spaces[start]),1.0))
  space_counts[int(spaces[start])]+=end-start;start=end
 for i in ids:seen[int(i)]+=1
 out=struct.pack('<8s5I',b'OARGEO1\0',nv,ni,len(ranges),76,48)+b''.join(ranges)+verts+indices
 assert out[28+48*len(ranges):]==verts+indices
 assert len(out)==28+48*len(ranges)+76*nv+4*ni
 (O/fn).write_bytes(out)
 files.append(dict(file=fn,input_sha256=sha(b),sha256=sha(out),cell=[cx,cy],vertices=nv,triangles=nt,ranges=len(ranges),bytes=len(out),geometry_index_payload_byteexact=True,spaces=sorted(set(int(x) for x in spaces))))
assert sum(space_counts.values())==51831 and all(seen[i]==s['triangles'] for i,s in enumerate(source))
report=dict(status='isolated ownership candidate; requires native Space visibility selector before promotion',files=files,cells=nc,triangles=51831,source_parts=590,source_owner_one_to_one=True,space_triangle_counts=dict(space_counts),ranges=sum(f['ranges'] for f in files),bytes=sum(f['bytes'] for f in files),material_count=mc,source_field='native SPACE assetID, gated by range flag0x40000000',limits=['No LOD geometry/range/transform changes; dense mode must bypass Space gate.','This metadata alone is not a fix; runtime must construct view admission from source portals.','Existing Region/shadow/waterfall bytes remain unchanged.'])
(Q/'ownership-stage.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))
