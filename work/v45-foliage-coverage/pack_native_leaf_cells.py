from pathlib import Path
import numpy as np,json,struct,hashlib,collections
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');Q=Path(__file__).resolve().parent;W=P/'work/v40-windows-host/assets/world';F=Q/'expanded-leaf-attributes';O=Q/'native-leaf-pack/world';O.mkdir(parents=True,exist_ok=True)
DT=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')]);OLD=np.dtype([('p','<f4',(3,)),('n','<i2',(4,)),('uv','<f4',(2,))]);maps={0:293,6:294,8:295};oldids=set(maps)|set(maps.values());rows=[];tot=collections.Counter();inputs=[]
manifest=json.loads((F/'fine-overlay-manifest.json').read_text());assert manifest['totals']['unmatched']==manifest['totals']['ambiguous']==0
for cx,cy in json.loads((Q/'visible-cells.json').read_text()):
 name=f'c{cx}_{cy}_0.bin';original=W/name;src=F/'fine-overlays'/name
 if not src.exists():src=original
 b=src.read_bytes();magic,nv,ni,nd=struct.unpack_from('<4s3I',b);off=16+12*nd;dr=[struct.unpack_from('<3I',b,16+12*j) for j in range(nd)]
 if magic!=b'OAWE':
  assert all(m not in oldids for m,f,n in dr),(name,'legacy leaf not joined');continue
 v=np.frombuffer(b,DT,nv,off);ix=np.frombuffer(b,'<u4',ni,off+nv*76);parts=[];draws=[];indices=[];nvnew=0;ninew=0
 for mat,first,count in dr:
  assert mat not in maps,(name,'unconverted leaf')
  if mat not in maps.values():continue
  soup=v[ix[first:first+count]];u,inv=np.unique(soup,return_inverse=True);parts.append(u);draws.append((mat,ninew,len(inv)));indices.append(inv.astype('<u4')+nvnew);nvnew+=len(u);ninew+=len(inv);tot[str(mat)]+=len(inv)//3
 if not parts:continue
 vertices=np.concatenate(parts);ind=np.concatenate(indices);out=b'OAWE'+struct.pack('<3I',len(vertices),len(ind),len(draws))+b''.join(struct.pack('<3I',*x) for x in draws)+vertices.tobytes()+ind.tobytes();n=f'l{cx}_{cy}.bin';(O/n).write_bytes(out);rows.append((cx,cy,len(ind)//3));inputs.append({'source':str(src.relative_to(P)),'source_sha256':hashlib.sha256(b).hexdigest(),'file':n,'sha256':hashlib.sha256(out).hexdigest(),'triangles':len(ind)//3,'vertices':len(vertices)})
 # Byte-for-byte native vertex fields and original geometry+UV are preserved through deduplication.
 assert np.array_equal(vertices[ind],np.concatenate([v[ix[first:first+count]] for mat,first,count in dr if mat in maps.values()]))
head=b'OALF001\0'+struct.pack('<3I',len(rows),len(maps),296)+b''.join(struct.pack('<2I',*x) for x in maps.items())+b''.join(struct.pack('<iiI',*x) for x in rows);(O/'leaf-index.bin').write_bytes(head)
files={f.name:{'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in O.iterdir()};r={'cells':len(rows),'triangles':sum(t for x,y,t in rows),'material_triangles':dict(tot),'geometry_changed':False,'new_instances':0,'full_vertex_identity_verified':True,'legacy_to_native_materials':maps,'inputs':inputs,'files':files,'total_bytes':sum(x['bytes'] for x in files.values()),'scope':'Native source attributes on all203 currentfrustum cells; only proven existingleaftriangles, separate leaf cells preserve bodies/terrain and replace fallbackleafdraws whenready.'};(Q/'native-leaf-pack/manifest.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items() if k not in ['inputs','files']},indent=2))
