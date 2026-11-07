"""Merge independent source-geometry candidates without writing live assets."""
from pathlib import Path
import hashlib,json,struct,shutil,collections
import numpy as np
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');V=P/'work/v45-foliage-coverage';W=P/'work/v40-windows-host/assets/world'
REG=V/'instance-audit/tree-gap-producer';LAMP=V/'lamp-source-audit/stage';CART=V/'image-band-audit/left-bridge-structure';OUT=V/'integrated-source-stage';WORLD=OUT/'world';WORLD.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest={'status':'staged only, no live writes','source_inputs':[],'overrides':{},'new_files':{},'limits':['RegionLODdistanceScale0.5 is a captured-quality inference, not recovered native global setting','Cart FAB local-transform composition is numerically validated; general node ownership remains unproven','Existing legacy material profiles for some actor parts remain approximations'],'waterfalls':'Original waterfall files preserved; no geometry/material/shader edits'}

def put(name,data):
 p=WORLD/name;p.write_bytes(data);m={'bytes':len(data),'sha256':sha(data)}
 if (W/name).exists():m['before_sha256']=sha((W/name).read_bytes());manifest['overrides'][name]=m
 else:manifest['new_files'][name]=m

# Preserve original banks byte-for-byte, then append three reviewed native profiles.
b=(W/'materials.bin').read_bytes();n=struct.unpack_from('<I',b)[0];assert n==296 and len(b)==4+n*28
nb=(W/'native-materials.bin').read_bytes();assert nb[:8]==b'OANM001\0';nn=struct.unpack_from('<I',nb,8)[0];assert nn==296 and len(nb)==12+nn*84
mats=bytearray(b[4:]);profiles=bytearray(nb[12:])
for idx,mp,np_ in [(296,REG/'candidate-materials/material-296.row28',REG/'candidate-materials/native-material-296.row84'),(297,REG/'candidate-materials/material-297.row28',REG/'candidate-materials/native-material-297.row84'),(298,LAMP/'material-298.mats28.bin',LAMP/'material-298.native84.bin')]:
 a=mp.read_bytes();c=np_.read_bytes();assert len(a)==28 and len(c)==84;assert len(mats)//28==idx;assert len(profiles)//84==idx;mats+=a;profiles+=c
put('materials.bin',struct.pack('<I',299)+mats);put('native-materials.bin',b'OANM001\0'+struct.pack('<I',299)+profiles)
# Leaf map identity and ownership are unchanged; only final bank-size guard changes.
b=bytearray((W/'leaf-index.bin').read_bytes());assert b[:8]==b'OALF001\0' and struct.unpack_from('<I',b,16)[0]==296;struct.pack_into('<I',b,16,299);put('leaf-index.bin',b)
for directory in [REG/'candidate-materials',LAMP]:
 for p in sorted(directory.glob('t*.bin')):
  assert p.stem[1:].isdigit();idx=int(p.stem[1:]);assert 685<=idx<=696;data=p.read_bytes();assert data[:4]==b'OATX';put(p.name,data)

# A cell owns indexed source vertices/ranges. Preserve source-index namespaces.
cells=collections.defaultdict(list)
def read_region(path,source):
 b=path.read_bytes();assert b[:8]==b'OARGEO1\0';nv,ni,nr,vs,rs=struct.unpack_from('<5I',b,8);assert vs==76 and rs==48 and nr<=4096;assert len(b)==28+nr*48+nv*76+ni*4
 runs=bytearray(b[28:28+nr*48]);verts=b[28+nr*48:28+nr*48+nv*76];inds=np.frombuffer(b,dtype='<u4',count=ni,offset=28+nr*48+nv*76).copy();assert not ni or int(inds.max())<nv
 for j in range(nr):
  r=struct.unpack_from('<4I6fIf',runs,j*48);assert r[0]<299 and r[1]+r[2]<=ni and r[2]%3==0 and r[8]>=0 and r[9]>=r[8] and 0<=r[11]<=16
 coord=tuple(map(int,path.stem[1:].split('_')));cells[coord].append((nv,ni,nr,runs,verts,inds));manifest['source_inputs'].append({'source':source,'path':str(path),'sha256':sha(b),'vertices':nv,'triangles':ni//3,'ranges':nr})
for source,folder in [('region',REG/'candidate-world-full'),('lamps',LAMP/'lamp-world')]:
 assert folder.exists(),str(folder)
 for path in sorted(folder.glob('r*.bin')):
  if __import__('re').fullmatch(r'r-?\d+_-?\d+\.bin',path.name):read_region(path,source)

# A source actor plus a source FAB local transform; captured matrix only verifies it.
a=json.loads((CART/'aux-cart-runs.json').read_text());pose=next(x for x in a['poses'] if x['pose']=='source-actor-plus-FAB-local-candidate');f=CART/pose['indexed_file'];b=f.read_bytes();assert sha(b)==pose['indexed_sha256'];assert b[:4]==b'OAWE';nv,ni,nr=struct.unpack_from('<3I',b,4);assert nr==1 and len(b)==16+12+nv*76+ni*4;mat,first,count=struct.unpack_from('<3I',b,16);assert mat==10 and first==0 and count==ni
verts=b[28:28+nv*76];inds=np.frombuffer(b,dtype='<u4',count=ni,offset=28+nv*76).copy();assert int(inds.max())<nv
anchor=pose['world_matrix_column_major'][12:15];radius=float(np.linalg.norm(np.array(pose['world_bounds_max'])-np.array(pose['world_bounds_min']))/2);runs=bytearray(struct.pack('<4I6fIf',mat,0,ni,a['source_kind_raw'],*anchor,radius,0.,1.e20,0x50000000+a['source_instance_id'],1.))
cells[tuple(a['cell'])].append((nv,ni,nr,runs,verts,inds));manifest['source_inputs'].append({'source':'source actor plus FAB local transform','path':str(f),'sha256':sha(b),'vertices':nv,'triangles':ni//3,'ranges':nr})

rows=[];total_tris=total_draws=total_vertices=0
for (cx,cy),parts in sorted(cells.items()):
 vv=[];ii=[];rr=[];nv=ni=nr=0
 for pv,pi,pr,runs,verts,indices in parts:
  r=bytearray(runs)
  for j in range(pr):
   start=struct.unpack_from('<I',r,j*48+4)[0];struct.pack_into('<I',r,j*48+4,start+ni)
  rr.append(r);vv.append(verts);ii.append(indices+np.uint32(nv));nv+=pv;ni+=pi;nr+=pr
 assert nr<=4096
 vb=b''.join(vv);ib=np.concatenate(ii).astype('<u4').tobytes();rb=b''.join(rr)
 xyz=np.ndarray((nv,3),'<f4',vb,0,(76,4));assert np.isfinite(xyz).all();lo=xyz.min(0);hi=xyz.max(0)
 data=b'OARGEO1\0'+struct.pack('<5I',nv,ni,nr,76,48)+rb+vb+ib;put(f'r{cx}_{cy}.bin',data)
 rows.append(struct.pack('<iiII6f',cx,cy,ni//3,nr,*lo,*hi));total_tris+=ni//3;total_draws+=nr;total_vertices+=nv
put('region-index.bin',b'OARGIDX1'+struct.pack('<IIfI',len(rows),299,.5,0)+b''.join(rows))
manifest.update(cells=len(rows),vertices=total_vertices,stored_triangles_all_authored_LODs=total_tris,stored_ranges=total_draws,material_count=299,source_index_namespaces={'region':'0..2913','lamp':'0x40000000+source ordinal','cart':'0x50000000+source entity id'})
# Reparse every staged cell and require indices/ranges/bounds and unique source/LOD slices.
for (cx,cy),parts in sorted(cells.items()):
 b=(WORLD/f'r{cx}_{cy}.bin').read_bytes();nv,ni,nr,vs,rs=struct.unpack_from('<5I',b,8);assert len(b)==28+nr*rs+nv*vs+ni*4
 ix=np.frombuffer(b,dtype='<u4',count=ni,offset=28+nr*48+nv*76);assert int(ix.max())<nv
 starts=[]
 for j in range(nr):
  r=struct.unpack_from('<4I6fIf',b,28+j*48);assert r[0]<299 and r[1]+r[2]<=ni;starts.append((r[1],r[1]+r[2]))
 assert sorted(starts)==[(sum(z[1]-z[0] for z in sorted(starts)[:i]),sum(z[1]-z[0] for z in sorted(starts)[:i+1])) for i in range(len(starts))]
manifest['checks']={'all_cells_reparsed':True,'all_indices_bounded':True,'all_runs_disjoint_cover_index_buffer':True,'original_material_bank_prefix_preserved':bytes(mats[:296*28])==(W/'materials.bin').read_bytes()[4:],'original_native_profile_prefix_preserved':bytes(profiles[:296*84])==(W/'native-materials.bin').read_bytes()[12:]}
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({k:v for k,v in manifest.items() if k not in ['source_inputs','overrides','new_files']},indent=2))
