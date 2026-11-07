from pathlib import Path
import numpy as np,json,struct,collections,itertools,hashlib,time
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');Q=Path(__file__).resolve().parent;O=Q/'cell-overlays';O.mkdir(exist_ok=True)
raw=(Q/'leaf-source-attributes.oawt').read_bytes();_,ver,st,nv,ni=struct.unpack_from('<4s4I',raw);dt=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')]);a=np.frombuffer(raw,dt,offset=20);tri=a.reshape(-1,3);pos=tri['v'][:,:,:3];uv=tri['v'][:,:,12:14];cent=pos.mean(1);lut=collections.defaultdict(list)
# Exact geometry+UV triangle keys allow cyclic/reversed source ordering.
def key(p,u):return tuple(sorted(tuple(np.round(np.r_[x*.25,y*4096]).astype(np.int64)) for x,y in zip(p,u)))
for k,(p,u) in enumerate(zip(pos,uv)):lut[key(p,u)].append(k)
perms=list(itertools.permutations(range(3)));manifest=[];M=json.loads((Q/'native-materials.json').read_text());families=collections.Counter();total=0
for x,y in json.loads((Q/'attributes-manifest.json').read_text())['cells']:
 fn=f'c{x}_{y}_0.bin';path=P/'work/v40-windows-host/assets/world'/fn;b=path.read_bytes();magic,v,i,d=struct.unpack_from('<4s3I',b);assert magic==b'OAWC';vo=16+d*12;verts=np.frombuffer(b,np.dtype([('p','<f4',(3,)),('n','<i2',(4,)),('uv','<f4',(2,))]),v,vo);ix=np.frombuffer(b,'<u4',i,vo+v*28).reshape(-1,3);draws=[struct.unpack_from('<3I',b,16+z*12) for z in range(d)];out=[];remove=[];counts=collections.Counter();ambiguities=0;maxerr=0
 for t,ind in enumerate(ix):
  p=verts['p'][ind];u=verts['uv'][ind];cand=lut.get(key(p,u),[])
  if not cand:continue
  matches=[]
  for k in cand:
   for perm in perms:
    err=float(np.max(abs(p-pos[k,list(perm)])));ue=float(np.max(abs(u-uv[k,list(perm)])))
    if err<=.04 and ue<=.0001:matches.append((k,perm,err));break
  if not matches:continue
  mids={int(tri['material'][k,0]) for k,_,_ in matches}
  if len(mids)!=1:ambiguities+=1;continue
  k,perm,err=matches[0];vout=tri[k,list(perm)].copy();vout['v'][:,:3]=p;vout['v'][:,12:14]=u;out.append(vout);remove.append(t*3);maxerr=max(maxerr,err);mid=next(iter(mids));counts[(mid,M[str(mid)]['shader'])]+=1
 if out:
  corner=np.concatenate(out);blob=struct.pack('<4s4I',b'OAWT',1,76,len(corner),0)+corner.tobytes();(O/fn.replace('.bin','.oawt')).write_bytes(blob);(O/fn.replace('.bin','.remove.u32')).write_bytes(np.array(remove,'<u4').tobytes());total+=len(remove)
 row=dict(cell=[x,y],source_cell=fn,source_sha256=hashlib.sha256(b).hexdigest(),triangles=len(ix),joined=len(remove),ambiguous=ambiguities,max_position_error=maxerr,material_triangles=[dict(material=m,shader=s,triangles=c) for (m,s),c in counts.items()],overlay_bytes=20+len(remove)*3*76,remove_format='u32 offsets into original OAWC index array; each offset identifies3 original indices; rebuild draws excluding those triples; source vertex+index positions preserved in overlay')
 manifest.append(row);print(fn,'joined',len(remove),'of',len(ix),'ambiguous',ambiguities,'maxerr',maxerr,flush=True)
 for (m,s),c in counts.items():families[s]+=c
(Q/'cell-join-manifest.json').write_text(json.dumps(dict(total_joined=total,shader_counts=dict(families),cells=manifest,scope='LOD0 only; actual cell positions+UV copied unchanged; source material/TBN/RGBA/UV2 attached after source geometry match; shader implementation remains independent'),indent=2));print(total,families)
