from pathlib import Path
import json,struct,hashlib,collections,numpy as np,shutil
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');Q=P/'work/v44-native-fidelity/water-research/static-material-followup';OUT=Path(__file__).resolve().parent;BASE=P/'work/v40-windows-host/assets/world';O=OUT/'world-next';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();NONE=0xffffffff;dt=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')]);old_dt=np.dtype([('p','<f4',(3,)),('n','<i2',(4,)),('uv','<f4',(2,))]);M=json.loads((Q/'native-materials.json').read_text());native_ids=sorted(map(int,M));new_index={id:263+i for i,id in enumerate(native_ids)};plan={m['material']:m for m in json.loads((Q/'material-texture-plan.json').read_text())['materials']};extras=json.loads((Q/'extra-texture-manifest.json').read_text());extra_map={};extra_files=[];nexttex=658
for e in extras:
 if e['status']!='ready':continue
 tid=nexttex;nexttex+=1;src=Q/'extra-textures'/e['file'];raw=src.read_bytes();assert sha(raw)==e['sha256'];name=f't{tid}.bin';(O/name).write_bytes(raw);extra_map[(e['asset'],e['kind'])]=tid;extra_files.append(dict(texture=tid,file=name,source=e,sha256=sha(raw),bytes=len(raw)))
def texid(m,slot):
 row=next((x for x in plan[m]['maps'] if x['slot']==slot),None)
 if row is None:return NONE
 if row['existing_texture_index'] is not None:return row['existing_texture_index']
 return extra_map.get((row['asset'],row['kind']),NONE)
mb=(BASE/'materials.bin').read_bytes();oldcount=struct.unpack_from('<I',mb)[0];assert oldcount==263,oldcount;newcount=263+len(native_ids);rows=bytearray(mb[4:]);profiles=[struct.pack('<I8I12f',0,*([NONE]*8),*([1]*4),1,20,0,0,1,1,1,1) for _ in range(newcount)];oldlighting=(BASE/'material-lighting.bin').read_bytes();n=struct.unpack_from('<I',oldlighting,8)[0];assert oldlighting[:8]==b'OAML001\0'
for i in range(n):
 fam,*values=struct.unpack_from('<I8f',oldlighting,12+i*36)
 if fam:flags,*tx=struct.unpack_from('<7I',mb,4+i*28);profiles[i]=struct.pack('<I8I12f',fam,*(tx[:3]+[NONE]*5),*values,1,1,1,1)
# Root merges the reserved native-grass rows/textures separately.
profiles[254]=struct.pack('<I8I12f',5,655,656,657,*([NONE]*5),1,1,1,1,1,20,0,0,1,1,1,1)
mat_receipt=[]
for id in native_ids:
 m=M[str(id)];fam={'dot3':1,'trunkdot3':2,'vertexblend':3,'vertexblendmodifiedmask':4}[m['shader']];tx=[texid(id,s) for s in [0,3,2,8,11,10,1,9]];par={x['key']:x['value'] for x in m['params']};color=par.get(10276250,[1.,1.,1.,1.]);spec=par.get(11960536,[1.,20.,0.,0.]);uv=[par.get(k,[1.])[0] for k in [883724,884831,1122436,1123543]];index=new_index[id];rows+=struct.pack('<7I',0x8000,*tx[:6]);profiles[index]=struct.pack('<I8I12f',fam,*tx,*color,*spec,*uv);mat_receipt.append(dict(native_material=id,index=index,shader=m['shader'],family=fam,textures=tx,color=color,specular=spec,tiling=uv,source=m['path'],source_sha256=m['sha256']))
(O/'materials.bin').write_bytes(struct.pack('<I',newcount)+rows);(O/'native-materials.bin').write_bytes(b'OANM001\0'+struct.pack('<I',newcount)+b''.join(profiles));water=(BASE/'water.bin').read_bytes();assert struct.unpack_from('<I',water)[0]==oldcount;(O/'water.bin').write_bytes(struct.pack('<I',newcount)+water[4:]+b'\0'*((newcount-oldcount)*44));index=bytearray((BASE/'index.bin').read_bytes());struct.pack_into('<I',index,12,max(struct.unpack_from('<I',index,12)[0],nexttex));(O/'index.bin').write_bytes(index)
# Match all original-world river triangles, including every duplicate source copy.
def trikey(p,u):return tuple(sorted(tuple(float(z) for z in np.r_[x,y]) for x,y in zip(p,u)))
water_keys=collections.defaultdict(set);candidate_cells=set();water_prov=json.loads((Q/'legacy-water-hide-provenance.json').read_text())
for m in water_prov:
 b=(Q/'water-hide'/m['file']).read_bytes();_,_,_,_,nv,ni,_,_=struct.unpack_from('<4s7I',b);v=np.frombuffer(b,'<f4',nv*18,32).reshape(-1,18);ix=np.frombuffer(b,'<u4',ni,32+nv*72).reshape(-1,3)
 for tri in ix:
  p=v[tri,:3];u=v[tri,3:5];water_keys[(m['legacy_material'],trikey(p,u))].add(m['draw']);cx,cy=np.floor(p.mean(0)[:2]/6400).astype(int)
  for x in range(cx-1,cx+2):
   for y in range(cy-1,cy+2):candidate_cells.add((x,y))
# Reproduce exact original source-cell ownership and build per-key multiplicity budgets.
source_removals=json.loads((Q/'legacy-water-zone-removals.json').read_text());source_pos=np.load(P/'work/v22-stress/zone-dal/zone_pos.npy',mmap_mode='r').reshape(-1,3,3);source_uv=np.load(P/'work/v22-stress/zone-dal/zone_uv.npy',mmap_mode='r').reshape(-1,3,2);source_tex=np.load(P/'work/v22-stress/zone-dal/zone_tex.npy',mmap_mode='r');water_budget=[collections.defaultdict(collections.Counter) for _ in range(3)];expected=collections.Counter()
def original_cell(p):
 sums=p[0,:2]+p[1,:2]+p[2,:2];cell=np.floor(np.floor(sums)/3/6400).astype(int);return (int(cell[0]),int(cell[1]))
for m in source_removals:
 for tid in m['legacy_triangle_indices']:
  p=source_pos[tid];u=source_uv[tid];cell=original_cell(p);candidate_cells.add(cell);key=(cell,m['legacy_material'],trikey(p,u));water_budget[0][key][m['draw']]+=1;expected[(m['draw'],0)]+=1
for lod in [1,2]:
 cache=np.load(OUT/'lod-cache'/f'water-lod{lod}.npz')
 for z in np.flatnonzero(cache['keep']):
  tid=int(cache['global_triangles'][z]);cell=original_cell(source_pos[tid]);candidate_cells.add(cell);draw=int(cache['draw'][z]);mat=int(cache['material'][z]);key=(cell,mat,trikey(cache['positions'][z],cache['uv'][z]));water_budget[lod][key][draw]+=1;expected[(draw,lod)]+=1
static=json.loads((Q/'cell-join-manifest.json').read_text());static_by_cell={tuple(m['cell']):m for m in static['cells']};candidate_cells|=set(static_by_cell);receipts=[];water_counts=collections.Counter();total=collections.Counter()
for x,y in sorted(candidate_cells):
 for lod in range(3):
  name=f'c{x}_{y}_{lod}.bin';path=BASE/name
  if not path.exists():continue
  b=path.read_bytes();magic,nv,ni,nd=struct.unpack_from('<4s3I',b)
  if magic!=b'OAWC':raise RuntimeError((name,magic,'baseline changed; preserve and coordinate with root'))
  draws=[struct.unpack_from('<3I',b,16+i*12) for i in range(nd)];vo=16+nd*12;v=np.frombuffer(b,old_dt,nv,vo);inds=np.frombuffer(b,'<u4',ni,vo+nv*28);remove=set();static_records=[];static_draws=collections.OrderedDict()
  if lod==0 and (x,y) in static_by_cell:
   src=static_by_cell[(x,y)];assert sha(b)==src['source_sha256'],(name,'source cell changed after join');overlay=(Q/'cell-overlays'/name.replace('.bin','.oawt')).read_bytes();ov=np.frombuffer(overlay,dt,offset=20).reshape(-1,3);offsets=np.fromfile(Q/'cell-overlays'/name.replace('.bin','.remove.u32'),'<u4');assert len(ov)==len(offsets)
   for tri,offset in zip(ov,offsets):
    assert np.array_equal(tri['v'][:,:3],v['p'][inds[offset:offset+3]]) and np.array_equal(tri['v'][:,12:14],v['uv'][inds[offset:offset+3]])
    remove.add(int(offset));mid=int(tri['material'][0]);static_draws.setdefault(new_index[mid],[]).append(tri.copy());total['static_source_triangles']+=1
  river_removed=collections.Counter()
  for material,first,count in draws:
   if material not in [62,63,64,206]:continue
   for offset in range(first,first+count,3):
    tri=inds[offset:offset+3];key=((x,y),material,trikey(v['p'][tri],v['uv'][tri]));budget=water_budget[lod].get(key)
    if budget:
     draw=next((d for d,n in budget.items() if n>0),None)
     if draw is not None:
      budget[draw]-=1;remove.add(offset);river_removed[draw]+=1;water_counts[(draw,lod)]+=1
  if not remove:continue
  expanded=np.zeros(nv,dt);expanded['v'][:,:3]=v['p'];expanded['v'][:,3:6]=v['n'][:,:3].astype(np.float32)/32767.*(v['n'][:,3:4].astype(np.float32)/32767.);expanded['v'][:,12:14]=v['uv'];expanded['v'][:,14:16]=v['uv'];expanded['rgba'][:]=255
  outdraw=[];outinds=[];cursor=0;kept_before=0
  for material,first,count in draws:
   chunks=[inds[i:i+3] for i in range(first,first+count,3) if i not in remove]
   if chunks:
    keep=np.concatenate(chunks).astype('<u4');outdraw.append((material,cursor,len(keep)));outinds.append(keep);cursor+=len(keep);kept_before+=len(keep)//3
  more=[];vn=nv
  for mid,tris in static_draws.items():
   corner=np.concatenate(tris);more.append(corner);idx=np.arange(vn,vn+len(corner),dtype='<u4');outdraw.append((mid,cursor,len(idx)));outinds.append(idx);cursor+=len(idx);vn+=len(corner)
  vertices=np.concatenate([expanded]+more);indices=np.concatenate(outinds) if outinds else np.empty(0,'<u4');assert np.array_equal(vertices['v'][:nv,:3],v['p']);assert np.array_equal(vertices['v'][:nv,12:14],v['uv']);assert len(indices)%3==0 and (len(indices)==0 or indices.max()<len(vertices));assert np.isfinite(vertices['v']).all();assert len(outdraw)<=128,(name,len(outdraw));blob=b'OAWE'+struct.pack('<3I',len(vertices),len(indices),len(outdraw))+b''.join(struct.pack('<3I',*d) for d in outdraw)+vertices.tobytes()+indices.tobytes();(O/name).write_bytes(blob);total['cells']+=1;total['retained_baseline_triangles']+=kept_before;total['water_removed_triangles']+=sum(river_removed.values());receipts.append(dict(cell=[x,y],lod=lod,file=name,input_sha256=sha(b),sha256=sha(blob),bytes=len(blob),old_vertices=nv,new_vertices=len(vertices),old_indices=ni,new_indices=len(indices),old_draws=nd,new_draws=len(outdraw),static_joined=sum(len(t) for t in static_draws.values()),water_removed=dict(river_removed),retained_old_triangles=kept_before,baseline_positions_uv_preserved=True,baseline_material_draw_order_preserved=True))
assert water_counts==expected,('Coarse/source water mismatch',expected-water_counts,water_counts-expected)
files={f.name:dict(bytes=f.stat().st_size,sha256=sha(f.read_bytes())) for f in O.iterdir()};receipt=dict(generation=2,all_lod_water_expected=[dict(draw=d,lod=l,count=c) for (d,l),c in sorted(expected.items())],all_lod_water_exact_matched=True,format='OAWE same16B cellheader/drawrec12; vertex76 OAWT fields; u32indices',totals=dict(total),material_count=newcount,old_material_count=oldcount,new_material_indices=mat_receipt,textures_reserved=[655,656,657],texture_count=nexttex,extra_textures=extra_files,water_removed_by_draw_lod=[dict(draw=d,lod=l,count=c) for (d,l),c in sorted(water_counts.items())],cells=receipts,files=files,old_material_rows_preserved=bytes(rows[:len(mb)-4])==mb[4:],index_record_bytes_preserved=bytes(index[20:])==(BASE/'index.bin').read_bytes()[20:],index_only_texture_count_updated=True,limits=['grass g/index grass updates intentionally untouched; root must merge reserved655..657','LOD1/2 staticattrs baseline; water source ownership recovered by exact original whole-zone cluster and source cell','baseline normal length preserves old packed normal.w vertexalpha; shader uses length(N) forflags0','tangent defaults zero forbaselineflags0 derivativefallback','native-materials.bin contains all293profiles; legacy OAML file untouched inbase','no source orexistingassetwrites']);(OUT/'manifest-next.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(dict(totals=receipt['totals'],materials=newcount,textures=nexttex,water=receipt['water_removed_by_draw_lod'],cells=len(receipts)),indent=2))
