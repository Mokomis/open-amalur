"""Propagate source-correlated attributes through the existing port's LOD ancestry.
No geometry generation policy change and no active pack mutation.
"""
from pathlib import Path
import numpy as np,json,struct,collections,itertools,hashlib,time
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent
F=Q.parent;S=P/'work/v22-stress/zone-dal';A=P/'work/v44-native-fidelity/water-research/static-material-followup'
O=Q/'cell-overlays';O.mkdir(exist_ok=True);C=Q/'lod-cache';C.mkdir(exist_ok=True)
DT=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')]);assert DT.itemsize==76
cells=[tuple(c) for c in json.loads((F/'attributes-manifest.json').read_text())['cells']]
source=[];inputs=[]
for root in [A,F]:
 for cell in cells:
  f=root/'cell-overlays'/f'c{cell[0]}_{cell[1]}_0.oawt'
  if not f.exists():continue
  b=f.read_bytes();magic,version,stride,nv,ni=struct.unpack_from('<4s4I',b)
  assert (magic,version,stride,ni)==(b'OAWT',1,76,0) and len(b)==20+76*nv
  source.append(np.frombuffer(b,DT,offset=20).copy().reshape(-1,3))
  inputs.append(dict(path=str(f),sha256=hashlib.sha256(b).hexdigest(),triangles=nv//3))
T=np.concatenate(source);sourceuv=np.concatenate([T['v'][:,:,:3],T['v'][:,:,12:14]],2).astype('<f4')
def key(a):return b''.join(sorted(a[i].tobytes() for i in range(3)))
lut=collections.defaultdict(list)
for k,row in enumerate(sourceuv):lut[key(row)].append(k)
audit=json.loads((P/'work/v44-native-fidelity/material-audit/material-candidates.json').read_text())
legacy=collections.defaultdict(set)
for r in audit['rows']:
 for c in r['candidates']:legacy[c['id']].add(r['index'])
allowed=set(int(x) for x in np.unique(T['material']));legacy_supported=set().union(*(legacy[x] for x in allowed))
pos=np.load(S/'zone_pos.npy',mmap_mode='r');uv=np.load(S/'zone_uv.npy',mmap_mode='r');tex=np.load(S/'zone_tex.npy',mmap_mode='r')
assert len(pos)==len(uv)==3*len(tex)
cellids={c:[] for c in cells};start=time.time()
# Reproduce original cell ownership exactly: floor(sum) before division.
for first in range(0,len(tex),500000):
 n=min(500000,len(tex)-first);v=pos[first*3:(first+n)*3].reshape(-1,3,3)
 x=np.floor(np.floor(v[:,0,0]+v[:,1,0]+v[:,2,0])/3/6400).astype(np.int32)
 y=np.floor(np.floor(v[:,0,1]+v[:,1,1]+v[:,2,1])/3/6400).astype(np.int32)
 for c in cells:
  ids=np.flatnonzero((x==c[0])&(y==c[1]))+first
  if len(ids):cellids[c].append(ids)
cellids={c:np.concatenate(v) for c,v in cellids.items()}
print('ownership',sum(map(len,cellids.values())),'triangles',round(time.time()-start,2),'sec',flush=True)
gids=[];attr=[];gcell=[];ambiguities=[];missing=0;perms=list(itertools.permutations(range(3)))
for c in cells:
 candidates=cellids[c][np.isin(tex[cellids[c]],list(legacy_supported))]
 for gid in candidates:
  vid=gid*3+np.arange(3);row=np.concatenate([pos[vid],uv[vid]],1).astype('<f4');choices=lut.get(key(row),[])
  if not choices:missing+=1;continue
  matches=[]
  for k in choices:
   if int(tex[gid]) not in legacy[int(T['material'][k,0])]:continue
   for perm in perms:
    if np.array_equal(sourceuv[k,list(perm)],row):matches.append(T[k,list(perm)].copy());break
  if not matches:missing+=1;continue
  if any(not np.array_equal(m,matches[0]) for m in matches[1:]):
   ambiguities.append(dict(global_triangle=int(gid),cell=c,candidates=len(matches)));continue
  gids.append(int(gid));attr.append(matches[0]);gcell.append(c)
 print('ancestors',c,'source-owned',len(candidates),'matched-running',len(gids),flush=True)
gids=np.array(gids,np.int64);V=np.stack(attr);gc=np.array(gcell,np.int32);assert len(np.unique(gids))==len(gids)
np.savez(C/'fullres-ancestors.npz',global_triangles=gids,attributes=V,cell=gc)
report=dict(scope='Native shader-attribute propagation over existing port global-cluster LOD geometry; not original-game LOD geometry',source_triangles=len(T),source_native_materials=sorted(allowed),mapped_global_ancestors=len(gids),eligible_unmapped=missing,ambiguous=ambiguities,inputs=inputs,source_zone=dict(path=str(S),triangles=len(tex),vertices=len(pos)),lods=[])
vid=(gids[:,None]*3+np.arange(3)).reshape(-1)
for lod,grid in [(1,400.0),(2,1600.0)]:
 start=time.time();cache=C/f'attributes-lod{lod}.npz'
 if cache.exists() and 'global_triangles' in np.load(cache).files and np.array_equal(np.load(cache)['global_triangles'],gids):
  z=np.load(cache);coarse=z['positions'];keep=z['keep'];global_keep=z['global_keep'];groups=int(z['groups'])
 else:
  k=np.floor(pos/grid).astype(np.int64);k=(k[:,0]+(1<<20))|((k[:,1]+(1<<20))<<21)|((k[:,2]+(1<<20))<<42)
  _,inverse=np.unique(k,return_inverse=True);del k;groups=int(inverse.max())+1
  weights=np.bincount(inverse,minlength=groups).astype(np.float64)
  coords=np.stack([np.bincount(inverse,pos[:,i],groups)/weights for i in range(3)],1).astype('<f4')
  coarse=coords[inverse[vid]].reshape(-1,3,3);tr=inverse.reshape(-1,3)
  global_keep=(tr[:,0]!=tr[:,1])&(tr[:,1]!=tr[:,2])&(tr[:,0]!=tr[:,2]);keep=global_keep[gids]
  np.savez(cache,positions=coarse,keep=keep,global_keep=global_keep,groups=np.array(groups),global_triangles=gids)
  del inverse,weights,coords,tr
 print('cluster',lod,'kept',int(keep.sum()),'of',len(gids),'seconds',round(time.time()-start,2),flush=True)
 lr=dict(lod=lod,grid=grid,global_groups=groups,kept_source_ancestors=int(keep.sum()),dropped_degenerate_source_ancestors=int((~keep).sum()),cells=[])
 for c in cells:
  f=P/'work/v40-windows-host/assets/world'/f'c{c[0]}_{c[1]}_{lod}.bin';b=f.read_bytes();magic,nv,ni,nd=struct.unpack_from('<4s3I',b);off=16+12*nd
  if magic==b'OAWC':
   dt=np.dtype([('p','<f4',(3,)),('n','<i2',(4,)),('uv','<f4',(2,))]);av=np.frombuffer(b,dt,nv,off);ap=av['p'];au=av['uv'];stride=28
  elif magic==b'OAWE':
   av=np.frombuffer(b,DT,nv,off);ap=av['v'][:,:3];au=av['v'][:,12:14];stride=76
  else:raise AssertionError((f,magic))
  assert len(b)==off+nv*stride+ni*4;ix=np.frombuffer(b,'<u4',ni,off+nv*stride)
  draws=[struct.unpack_from('<3I',b,16+i*12) for i in range(nd)];drawmap={}
  for m,first,count in draws:drawmap.setdefault(m,(first,count))
  targets=np.flatnonzero(keep&(gc[:,0]==c[0])&(gc[:,1]==c[1]));mapped=[];rem=[];unmatched=[];anc=[]
  for m in sorted(set(int(tex[gids[k]]) for k in targets)):
   full=cellids[c][tex[cellids[c]]==m];retained=full[global_keep[full]]
   selected=targets[tex[gids[targets]]==m]
   if m not in drawmap:
    unmatched.extend(gids[selected].tolist());continue
   first,count=drawmap[m]
   for k in selected:
    rank=int(np.searchsorted(retained,gids[k]));assert rank<len(retained) and retained[rank]==gids[k]
    indoff=first+rank*3
    if indoff+3>first+count:unmatched.append(int(gids[k]));continue
    indices=ix[indoff:indoff+3];p=ap[indices];u=au[indices]
    if not np.array_equal(p,coarse[k]) or not np.array_equal(u,V['v'][k,:,12:14]):
     unmatched.append(int(gids[k]));continue
    v=V[k].copy();v['v'][:,:3]=p;v['v'][:,12:14]=u
    assert v['v'][:,3:12].tobytes()==V['v'][k,:,3:12].tobytes()
    assert v['v'][:,14:16].tobytes()==V['v'][k,:,14:16].tobytes()
    assert v['rgba'].tobytes()==V['rgba'][k].tobytes() and v['flags'].tobytes()==V['flags'][k].tobytes()
    mapped.append(v);rem.append(indoff);anc.append(int(gids[k]))
  order=np.argsort(rem);rem=np.array(rem,'<u4')[order];assert len(np.unique(rem))==len(rem)
  corner=np.stack(mapped)[order].reshape(-1).copy() if mapped else np.empty(0,DT)
  name=f'c{c[0]}_{c[1]}_{lod}';blob=struct.pack('<4s4I',b'OAWT',1,76,len(corner),0)+corner.tobytes()
  (O/(name+'.oawt')).write_bytes(blob);(O/(name+'.remove.u32')).write_bytes(rem.tobytes())
  counts=collections.Counter(int(x) for x in corner['material'][::3])
  row=dict(cell=c,source_cell=f.name,source_cell_sha256=hashlib.sha256(b).hexdigest(),source_magic=magic.decode(),source_triangles=ni//3,eligible_surviving_ancestors=len(targets),joined=len(mapped),unmatched_global_triangles=unmatched,positions_uv0_exact=True,normal_tangent_binormal_color_wind_material_preserved=True,native_material_triangles=dict(counts),output_sha256=hashlib.sha256(blob).hexdigest(),ancestor_global_triangles=np.array(anc,np.int64)[order].tolist())
  lr['cells'].append(row);print('cell',name,'joined',len(mapped),'/',len(targets),'unmatched',len(unmatched),flush=True)
 report['lods'].append(lr)
(Q/'lod-attribute-manifest.json').write_text(json.dumps(report,indent=2))
print('COMPLETE',[(l['lod'],sum(c['joined'] for c in l['cells']),sum(len(c['unmatched_global_triangles']) for c in l['cells'])) for l in report['lods']],flush=True)
