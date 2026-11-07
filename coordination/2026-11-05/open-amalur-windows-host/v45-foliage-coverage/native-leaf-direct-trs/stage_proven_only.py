"""Restrict the preserved full candidate to individually captured native poses."""
from pathlib import Path
import json,struct,hashlib,collections
import numpy as np
Q=Path(__file__).resolve().parent;O=Q/'proven-world';O.mkdir(exist_ok=True)
r=json.loads((Q/'manifest.json').read_text());guard=json.loads((Q/'transform-bounds-guard.json').read_text());offsets=json.loads((Q/'source-instance-offsets.json').read_text());chosen=set(guard['individually_native_matrix_proven_changes']['source_indices']);assert chosen=={457,458,467,468,484}
owner=np.concatenate([np.full(s['triangles'],s['source_instance'],int) for s in offsets]);rows=[];tot=collections.Counter();bounds=[]
for f in r['files']:
 old=(Q/'input-world'/f['file']).read_bytes();full=(Q/'world'/f['file']).read_bytes();_,nv,ni,nd=struct.unpack_from('<4s3I',old);start=16+12*nd
 a=np.frombuffer(old,'u1',nv*76,start).reshape(nv,76);b=np.frombuffer(full,'u1',nv*76,start).reshape(nv,76);ix=np.frombuffer(old,'<u4',ni,start+nv*76).reshape(-1,3);out=a.copy()
 selected=np.array([owner[k] in chosen for k in f['source_triangles']]);assert len(selected)==ni//3
 ids=np.unique(ix[selected]);out[ids]=b[ids]
 expected=a[ix].copy();expected[selected]=b[ix[selected]];assert np.array_equal(out[ix],expected),(f['file'],'shared vertex ownership conflict')
 blob=old[:start]+out.tobytes()+old[start+nv*76:];(O/f['file']).write_bytes(blob)
 tot['triangles']+=ni//3;tot['selected_triangles']+=int(selected.sum());tot['changed_vertices']+=int(np.any(out!=a,axis=1).sum())
 p=out[:,:12].copy().view('<f4').reshape(nv,3);lo=p.min(0);hi=p.max(0)
 rows.append(dict(file=f['file'],cell=f['cell'],triangles=ni//3,selected_triangles=int(selected.sum()),changed=blob!=old,bytes=len(blob),input_sha256=hashlib.sha256(old).hexdigest(),output_sha256=hashlib.sha256(blob).hexdigest(),bounds=[lo.tolist(),hi.tolist()]))
index=(Q/'input-world/leaf-index.bin').read_bytes();assert struct.unpack_from('<I',index,16)[0]==299;(O/'leaf-index.bin').write_bytes(index)
P=Path.home()/'Documents/Opem Amalur';W=P/'work/v40-windows-host/assets/world';base=(W/'index.bin').read_bytes();union={}
for i in range(struct.unpack_from('<I',base,8)[0]):
 at=20+i*48;union[struct.unpack_from('<2i',base,at)]=np.array(struct.unpack_from('<6f',base,at+8)).reshape(2,3)
reg=(W/'region-index.bin').read_bytes()
for i in range(struct.unpack_from('<I',reg,8)[0]):
 at=24+i*40;cell=struct.unpack_from('<2i',reg,at);b=np.array(struct.unpack_from('<6f',reg,at+16)).reshape(2,3)
 if cell in union:b=np.stack([np.minimum(b[0],union[cell][0]),np.maximum(b[1],union[cell][1])])
 union[cell]=b
for f in rows:
 old=union[tuple(f['cell'])];b=np.array(f['bounds'])
 if np.any(b[0]<old[0]) or np.any(b[1]>old[1]):bounds.append(dict(cell=f['cell'],old_union_bounds=old.tolist(),leaf_bounds=b.tolist(),required_union_bounds=[np.minimum(b[0],old[0]).tolist(),np.maximum(b[1],old[1]).tolist()]))
assert tot['triangles']==51831 and tot['selected_triangles']==331
report=dict(status='Individually native-observed matrix corrections only; full candidate retained separately',selected_source_indices=sorted(chosen),counts=dict(tot),cells=len(rows),changed_cells=sum(f['changed'] for f in rows),material_count=299,index_sha256=hashlib.sha256(index).hexdigest(),bytes=sum(f['bytes'] for f in rows)+len(index),bounds_expansion_cells=len(bounds),bounds_union_input_sha256=dict(base=hashlib.sha256(base).hexdigest(),region=hashlib.sha256(reg).hexdigest()),files=rows,source_proof=guard['individually_native_matrix_proven_changes'],unobserved_generalization_status='73unobserved changedrecords blockedpendingactualproducer/bindsemantics evidence; notapprovedforpromotion, noquerylooprequested')
(Q/'proven-only-manifest.json').write_text(json.dumps(report,indent=2));(Q/'proven-only-bounds-expansion.json').write_text(json.dumps(bounds,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['files','source_proof']},indent=2))
