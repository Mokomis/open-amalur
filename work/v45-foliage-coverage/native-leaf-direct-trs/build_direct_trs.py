"""Preserve current leaf ownership/index topology; correct source-proven P/N/radius only."""
from pathlib import Path
import collections,hashlib,itertools,json,struct,sys
import numpy as np
sys.dont_write_bytecode=True
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent
F=P/'work/v45-foliage-coverage/expanded-leaf-attributes';W=P/'work/v40-windows-host/assets/world'
O=Q/'world';O.mkdir(exist_ok=True)
sys.path.insert(0,str(P/'work/v07-mesh'));import amalur_mesh
DT=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')])
def sha(b):return hashlib.sha256(b).hexdigest()
def qr(q,v):
 u=np.array(q[:3]);t=2*np.cross(u,v);return v+q[3]*t+np.cross(u,t)
def key(p,u):return tuple(sorted(tuple(np.round(np.r_[a*.25,b*4096]).astype('i8')) for a,b in zip(p,u)))
def uvkey(u,m):return (int(m),tuple(sorted(tuple(np.round(b*4096).astype('i8')) for b in u)))
raw=(F/'leaf-source-attributes.oawt').read_bytes();assert struct.unpack_from('<4s4I',raw)[:3]==(b'OAWT',1,76)
T=np.frombuffer(raw,DT,offset=20).reshape(-1,3);assert len(T)==51831
prov=json.loads((F/'source-provenance.json').read_text());assert len(prov)==590
cells=set(tuple(c) for c in json.loads((F/'attributes-manifest.json').read_text())['cells'])
newpos=np.empty((len(T),3,3),'<f4');newnormal=np.empty_like(newpos);radius=np.empty((len(T),3),'<f4');owner=np.empty(len(T),'<i4')
cache={};cursor=0;offsets=[]
for pi,s in enumerate(prov):
 path=P/s['mesh_path'];rr=bytes.fromhex(s['render_record_hex']);t=np.array(struct.unpack_from('<3f',rr,16));q=struct.unpack_from('<4f',rr,32);sc=np.array(struct.unpack_from('<3f',rr,48));cq=(-q[0],-q[1],-q[2],q[3]);sphere=np.array(struct.unpack_from('<4f',rr))
 if path not in cache:cache[path]=(amalur_mesh.parse_file(path),path.read_bytes())
 m,src=cache[path];assert sha(src)==s['mesh_sha256'];a=m['assemblies'][s['assembly']];vb=m['vertex_buffers'][a['vertex_buffer']]
 xyz=np.array(vb['positions'],float);ix=np.array(m['index_buffers'][a['index_buffer']]['indices'],int).reshape(-1,3)
 cl=qr(q,(sphere[:3]-t)[None,:])[0];old=qr(cq,cl+(xyz-cl)*sc)+t;direct=qr(cq,xyz*sc)+t
 cc=np.floor(old[ix].mean(1)[:,:2]/6400).astype(int);sel=np.array([tuple(c) in cells for c in cc]);ix=ix[sel];n=len(ix);assert n==s['triangles'];target=T[cursor:cursor+n]
 assert np.array_equal(old.astype('<f4')[ix],target['v'][:,:,:3]),(pi,'source oldP replay')
 assert np.all(target['material']==s['material'])
 newpos[cursor:cursor+n]=direct.astype('<f4')[ix]
 radial=direct-t;radial[:,2]-=s['center_z_offset']
 if s['normal_mode']<.5:radial[:,2]=0
 rradius=np.linalg.norm(radial,axis=1).astype('<f4');radial/=np.maximum(rradius[:,None],1e-9)
 newnormal[cursor:cursor+n]=radial.astype('<f4')[ix];radius[cursor:cursor+n]=rradius[ix];owner[cursor:cursor+n]=pi
 delta=qr(cq,(cl*(sc-1))[None,:])[0];assert np.max(np.abs((direct-old)-delta))<1e-8
 offsets.append(dict(source_instance=pi,space=s['space'],fab=s['fab'],assembly=s['assembly'],native_material=s['material'],triangles=n,scale=sc.tolist(),translation=t.tolist(),correction_cm=delta.tolist(),distance_cm=float(np.linalg.norm(delta)),source_render_record_hex=rr.hex()))
 cursor+=n
assert cursor==len(T)
lut=collections.defaultdict(list);ulut=collections.defaultdict(list)
for i,tr in enumerate(T):lut[key(tr['v'][:,:3],tr['v'][:,12:14])].append(i);ulut[uvkey(tr['v'][:,12:14],tr['material'][0])].append(i)
perms=list(itertools.permutations(range(3)));receipt=[];mapped=collections.Counter();failures=[];oldindex=(W/'leaf-index.bin').read_bytes();n,nm,mc=struct.unpack_from('<3I',oldindex,8);assert mc==299
registry=struct.unpack_from('<'+str(nm*2)+'I',oldindex,20);assert len(oldindex)==20+nm*8+n*12
base=(W/'index.bin').read_bytes();bounds={}
for i in range(struct.unpack_from('<I',base,8)[0]):
 at=20+i*48;cell=struct.unpack_from('<2i',base,at);bounds[cell]=np.array(struct.unpack_from('<6f',base,at+8)).reshape(2,3)
rindex=(W/'region-index.bin').read_bytes()
for i in range(struct.unpack_from('<I',rindex,8)[0]):
 at=24+i*40;cell=struct.unpack_from('<2i',rindex,at);b=np.array(struct.unpack_from('<6f',rindex,at+16)).reshape(2,3)
 if cell in bounds:b=np.stack([np.minimum(bounds[cell][0],b[0]),np.maximum(bounds[cell][1],b[1])])
 bounds[cell]=b
outside=[];total=0
for row in range(n):
 cx,cy,nt=struct.unpack_from('<iiI',oldindex,20+nm*8+row*12);file=f'l{cx}_{cy}.bin';b=(W/file).read_bytes();magic,nv,ni,nd=struct.unpack_from('<4s3I',b);assert magic==b'OAWE' and ni//3==nt
 start=16+12*nd;v=np.frombuffer(b,DT,nv,start);ix=np.frombuffer(b,'<u4',ni,start+nv*76);out=v.copy();assigned={};sourceids=[];maxerr=0
 for j in range(0,ni,3):
  vi=ix[j:j+3];tr=v[vi];p=tr['v'][:,:3];uv=tr['v'][:,12:14];mid=int(tr['material'][0]);matches=[]
  cand=lut.get(key(p,uv),[])
  for attempt in range(2):
   for k in cand:
    if T['material'][k,0]!=mid:continue
    for perm in perms:
     perm=list(perm);st=T[k,perm];err=float(np.max(np.abs(p-st['v'][:,:3])))
     if err<=.04 and np.max(np.abs(uv-st['v'][:,12:14]))<=.0001 and np.array_equal(tr['rgba'],st['rgba']) and np.array_equal(tr['v'][:,6:12],st['v'][:,6:12]) and np.array_equal(tr['v'][:,14:16].view('u4'),st['v'][:,14:16].view('u4')):
      changed=tr.copy();changed['v'][:,:3]=newpos[k,perm];changed['v'][:,3:6]=newnormal[k,perm];changed['flags']=radius[k,perm].copy().view('<u4');matches.append((changed,k,err));break
   if matches:break
   cand=ulut[uvkey(uv,mid)]
  if not matches:failures.append(dict(file=file,index_offset=j,reason='unmatched'));continue
  changed,k,err=matches[0]
  if any(not np.array_equal(changed,z[0]) for z in matches[1:]):failures.append(dict(file=file,index_offset=j,reason='ambiguous changed attributes'));continue
  # Authored repeated triangles may have identical complete old/new attributes.
  # Consume equivalent source occurrences individually; never collapse ownership.
  changed,k,err=min(matches,key=lambda z:(mapped[z[1]],z[1]))
  for index,newvertex in zip(vi,changed):
   index=int(index)
   if index in assigned:assert assigned[index]==newvertex.tobytes(),(file,index,'shared vertex conflict')
   assigned[index]=newvertex.tobytes();out[index]=newvertex
  mapped[k]+=1;sourceids.append(k);maxerr=max(maxerr,err)
 # Only P,N and radialLength bits can differ. Header, draw rows, index bytes unchanged.
 oldbytes=v.view('u1').reshape(nv,76);newbytes=out.view('u1').reshape(nv,76)
 assert np.array_equal(oldbytes[:,24:72],newbytes[:,24:72])
 blob=b[:start]+out.tobytes()+b[start+76*nv:];assert len(blob)==len(b)
 lo=out['v'][:,:3].min(0);hi=out['v'][:,:3].max(0);ub=bounds[(cx,cy)]
 if np.any(lo<ub[0]) or np.any(hi>ub[1]):outside.append(dict(cell=[cx,cy],old_union_bounds=ub.tolist(),leaf_bounds=[lo.tolist(),hi.tolist()],required_union_bounds=[np.minimum(lo,ub[0]).tolist(),np.maximum(hi,ub[1]).tolist()]))
 receipt.append(dict(file=file,cell=[cx,cy],triangles=nt,vertices=nv,input_sha256=sha(b),output_sha256=sha(blob),bytes=len(blob),old_join_max_error_cm=maxerr,source_triangles=sourceids,bounds=[lo.tolist(),hi.tolist()]))
 total+=nt
 # Delay all geometry writes until the entire pack is proven below.
 receipt[-1]['_blob']=blob
assert not failures,failures[:20]
assert total==51831 and set(mapped)==set(range(51831)) and all(x==1 for x in mapped.values()),('source triangle ownership',total,len(mapped),collections.Counter(mapped.values()))
for r in receipt:(O/r['file']).write_bytes(r.pop('_blob'))
index=bytearray(oldindex);struct.pack_into('<I',index,16,299);(O/'leaf-index.bin').write_bytes(index)
# Scope the native evidence: captured source-matched draws, not all590 authored records.
audit=json.loads((P/'work/v45-foliage-coverage/instance-audit/raw-render-translation-vs-native-audit.json').read_text());matched=[r for r in audit['rows'] if r['same_fab_basis_raw_translation_matched']]
assert len(matched)==92
proof=dict(matched_native_draws=92,translation_max_error_cm=max(r['best_same_fab_raw_translation']['raw_translation_distance_cm'] for r in matched),basis_max_error=max(r['best_same_fab_raw_translation']['basis_max_error'] for r in matched),scope='92capturedtreebody/leafdraws match sourceFAB/provenalias+rawtranslation+basis; sameconjugateQscale decoder applied590authoredleafrecords, not590runtimeobservations',draws=matched)
dist=np.array([x['distance_cm'] for x in offsets]);report=dict(status='isolated candidate; same51831triangles/590sourceinstances; no live writes',cells=n,triangles=total,instances=len(prov),vertices=sum(r['vertices'] for r in receipt),bytes=sum(r['bytes'] for r in receipt)+len(index),material_count=299,index_sha256=sha(index),source_ownership_one_to_one=True,invariant_fields='Header/draws/index topology unchanged; UV0,RGBA,rawTB,packedwind,NativeMID bytes24..71 unchanged. OnlyP,N,radialLength changed.',offset_distribution_cm=dict(min=float(dist.min()),median=float(np.median(dist)),p90=float(np.percentile(dist,90)),p99=float(np.percentile(dist,99)),max=float(dist.max()),nonzero_instances=int((dist>1e-6).sum())),native_proof=proof,files=receipt,bounds_union_input_sha256=dict(base=sha(base),region=sha(rindex)),bounds_expansion_cells=len(outside))
(Q/'manifest.json').write_text(json.dumps(report,indent=2));(Q/'source-instance-offsets.json').write_text(json.dumps(offsets,indent=2));(Q/'bounds-expansion.json').write_text(json.dumps(outside,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['files','native_proof']},indent=2))
