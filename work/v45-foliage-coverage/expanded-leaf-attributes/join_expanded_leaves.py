from pathlib import Path
import numpy as np,struct,json,collections,itertools,hashlib,time
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');Q=Path(__file__).resolve().parent;W=P/'work/v40-windows-host/assets/world';O=Q/'fine-overlays';O.mkdir(exist_ok=True)
DT=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')]);OLD=np.dtype([('p','<f4',(3,)),('n','<i2',(4,)),('uv','<f4',(2,))]);b=(Q/'leaf-source-attributes.oawt').read_bytes();assert struct.unpack_from('<4s4I',b)[:3]==(b'OAWT',1,76);T=np.frombuffer(b,DT,offset=20).reshape(-1,3);lut=collections.defaultdict(list);perms=list(itertools.permutations(range(3)));source={0:359202,6:419060,8:559590};alias={359202:293,419060:294,559590:295};rows=[];tot=collections.Counter();anc=[]
def key(p,u):return tuple(sorted(tuple(np.round(np.r_[a*.25,b*4096]).astype('i8')) for a,b in zip(p,u)))
for i,t in enumerate(T):lut[key(t['v'][:,:3],t['v'][:,12:14])].append(i)
for cx,cy in json.loads((Q/'attributes-manifest.json').read_text())['cells']:
 f=W/f'c{cx}_{cy}_0.bin';b=f.read_bytes();magic,nv,ni,nd=struct.unpack_from('<4s3I',b);dr=[struct.unpack_from('<3I',b,16+12*i) for i in range(nd)];off=16+12*nd
 if magic==b'OAWC':
  a=np.frombuffer(b,OLD,nv,off);pos=a['p'];uv=a['uv'];stride=28
 elif magic==b'OAWE':
  a=np.frombuffer(b,DT,nv,off);pos=a['v'][:,:3];uv=a['v'][:,12:14];stride=76
 else:raise AssertionError((f,magic))
 ix=np.frombuffer(b,'<u4',ni,off+nv*stride);joined=[];newdraws=[];idx=[];verts=[];offsets=[];amb=0;missing=0;maxerr=0;newn=nv
 for mat,first,count in dr:
  if mat not in source:
   newdraws.append((mat,sum(len(x) for x in idx),count));idx.append(ix[first:first+count].copy());continue
  keep=[];groups=collections.defaultdict(list)
  for j in range(first,first+count,3):
   ids=ix[j:j+3];p=pos[ids];u=uv[ids];matches=[]
   for k in lut.get(key(p,u),[]):
    if int(T['material'][k,0])!=source[mat]:continue
    for perm in perms:
     err=float(np.max(np.abs(p-T['v'][k,list(perm),:3])));ue=float(np.max(np.abs(u-T['v'][k,list(perm),12:14])))
     if err<=.04 and ue<=.0001:
      t=T[k,list(perm)].copy();t['v'][:,:3]=p;t['v'][:,12:14]=u;matches.append((t,err));break
   if not matches:keep.extend(ids);missing+=1;continue
   if any(not np.array_equal(t,matches[0][0]) for t,e in matches[1:]):keep.extend(ids);amb+=1;continue
   t,err=matches[0];groups[alias[source[mat]]].append(t);maxerr=max(maxerr,err);offsets.append(j);joined.append(t);anc.append((cx,cy,j,mat))
  if keep:newdraws.append((mat,sum(len(x) for x in idx),len(keep)));idx.append(np.asarray(keep,'<u4'))
  for newmat,tris in groups.items():
   vv=np.concatenate(tris);ii=np.arange(newn,newn+len(vv),dtype='<u4');newn+=len(vv);verts.append(vv);newdraws.append((newmat,sum(len(x) for x in idx),len(ii)));idx.append(ii)
 if not joined:tot['unchanged_cells']+=1;continue
 if magic==b'OAWC':
  expanded=np.zeros(nv,DT);expanded['v'][:,:3]=pos;expanded['v'][:,3:6]=a['n'][:,:3].astype('f4')/32767*(a['n'][:,3:4].astype('f4')/32767);expanded['v'][:,12:14]=uv;expanded['v'][:,14:16]=uv;expanded['rgba'][:]=255
 else:expanded=a.copy()
 v=np.concatenate([expanded]+verts);ind=np.concatenate(idx);assert len(ind)==ni and len(newdraws)<=128
 # Every output triangle retains original position/UV, per original draw ordering.
 oldkeys=collections.Counter(key(pos[ix[j:j+3]],uv[ix[j:j+3]]) for mat,first,n in dr if mat in source for j in range(first,first+n,3))
 newkeys=collections.Counter(key(v['v'][ind[j:j+3],:3],v['v'][ind[j:j+3],12:14]) for mat,first,n in newdraws if mat in source or mat in alias.values() for j in range(first,first+n,3))
 # Existing native draws also occur in input; remove them before this identity comparison.
 for mat,first,n in dr:
  if mat in alias.values():
   for j in range(first,first+n,3):newkeys.subtract([key(pos[ix[j:j+3]],uv[ix[j:j+3]])])
 assert +oldkeys==+newkeys,(f,'geometry identity')
 out=b'OAWE'+struct.pack('<3I',len(v),len(ind),len(newdraws))+b''.join(struct.pack('<3I',*r) for r in newdraws)+v.tobytes()+ind.tobytes();(O/f.name).write_bytes(out);corner=np.concatenate(joined);(Q/'cell-overlays').mkdir(exist_ok=True);(Q/'cell-overlays'/f.name.replace('.bin','.oawt')).write_bytes(struct.pack('<4s4I',b'OAWT',1,76,len(corner),0)+corner.tobytes())
 row={'file':f.name,'cell':[cx,cy],'source_sha256':hashlib.sha256(b).hexdigest(),'sha256':hashlib.sha256(out).hexdigest(),'joined':len(joined),'unmatched':missing,'ambiguous':amb,'max_position_error_cm':maxerr,'indices_unchanged_count':ni,'bytes':len(out)};rows.append(row);tot['cells']+=1;tot['joined']+=len(joined);tot['unmatched']+=missing;tot['ambiguous']+=amb
 print(f.name,'joined',len(joined),'missing',missing,'ambiguous',amb,flush=True)
(Q/'fine-overlay-manifest.json').write_text(json.dumps({'totals':dict(tot),'cells':rows,'scope':'Source-correlated native leaf attributes only; original per-triangle position/UV preserved, no new instances or triangle count change.'},indent=2));np.save(Q/'fine-join-ancestry.npy',np.asarray(anc,'<i8'));print(dict(tot),flush=True)
