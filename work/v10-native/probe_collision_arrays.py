from pathlib import Path
import struct,json,math,hashlib
r=Path.home()/'Documents/Opem Amalur';rows=[]
for archive in ['DATA_0.pak','patch_0.pak']:
 p=r/'work/scene-inputs-v09'/archive/'524858.collision_set_bin';b=p.read_bytes();groups=[]
 gp,gc=struct.unpack_from('<II',b,16)
 assert gc==5
 for i in range(gc):
  unknown0,unknown1,mp,mc=struct.unpack_from('<4I',b,gp+i*16);meshes=[]
  assert mc<=16
  for j in range(mc):
   tag,vp,vc,tp,tc=struct.unpack_from('<5I',b,mp+j*20)
   assert vc<=100000 and tc<=100000 and vp+vc*12<=len(b) and tp+tc*16<=len(b)
   vertices=[struct.unpack_from('<3f',b,vp+k*12) for k in range(vc)];triangles=[struct.unpack_from('<4I',b,tp+k*16) for k in range(tc)]
   meshes.append(dict(index=j,record_file_offset=mp+j*20,tag=tag,vertex_offset=vp,vertices=vc,triangle_offset=tp,triangles=tc,finite=all(math.isfinite(x) for v in vertices for x in v),bounds_min=[min(v[a] for v in vertices) for a in range(3)],bounds_max=[max(v[a] for v in vertices) for a in range(3)],index_min=min(t[a] for t in triangles for a in range(3)),index_max=max(t[a] for t in triangles for a in range(3)),triangle_word3=sorted(set(t[3] for t in triangles))[:30],vertex_sample=vertices[:3],triangle_sample=triangles[:3]))
  groups.append(dict(index=i,unknown=[unknown0,unknown1],mesh_offset=mp,meshes=meshes))
 rows.append(dict(archive=archive,sha256=hashlib.sha256(b).hexdigest(),scope='candidate arrays inferred from exact spans, not native-confirmed',groups=groups))
(r/'outputs/scene-v10/collision-arrays.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
