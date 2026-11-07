from pathlib import Path
import numpy as np,json,struct,collections,math,sys,hashlib,time
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');OUT=Path(__file__).resolve().parent;sys.path.insert(0,str(P/'work/v07-mesh'));import amalur_mesh
S=json.loads((P/'work/v20-inputs/symbols.json').read_text());audit=json.loads((P/'work/v44-native-fidelity/material-audit/material-candidates.json').read_text());mats={c['id']:c for r in audit['rows'] for c in r['candidates'] if c['shader'] in ['dot3','trunkdot3','vertexblend','vertexblendmodifiedmask']};cells={(x,y) for x in range(-1,2) for y in range(-11,-8)}|{(x,y) for x in range(0,3) for y in range(-15,-12)}
def find(name):
 return next((P/'work/v20-inputs'/a/name for a in ['patch_0.pak','initial_0.pak','DATA_0.pak'] if (P/'work/v20-inputs'/a/name).exists()),None)
def qr(q,v):
 u=np.array(q[:3]);t=2*np.cross(u,v);return v+q[3]*t+np.cross(u,t)
cache={};chunks=[];prov=[];counts=collections.Counter();start=time.time()
for sid,sname in S['simspace'].items():
 if not sname.startswith('out_dal_'):continue
 path=find(sid+'.space_bxml')
 if not path:continue
 raw=path.read_bytes();pl=struct.unpack_from('<I',raw)[0];b=raw[8:8+pl]
 def arr(slot,stride):
  ptr,n=struct.unpack_from('<II',b,slot);assert ptr-8+n*stride<=len(b);return [b[ptr-8+i*stride:ptr-8+(i+1)*stride] for i in range(n)]
 refs=[struct.unpack('<I',r)[0] for r in arr(0x1b0,4)];centers=[struct.unpack('<3f',r) for r in arr(0x1a8,12)];renders=arr(0x160,84);bycenter={tuple(round(x,2) for x in struct.unpack_from('<3f',r)):r for r in renders};instances=[]
 for typed,center in zip(refs,centers):
  r=bycenter.get(tuple(round(x,2) for x in center))
  if r is not None and str(typed&0xfffffff) in S['fab']:instances.append((typed&0xfffffff,r,'refs'))
 for a,r in zip(arr(0x148,80),arr(0x150,84)):
  fab=struct.unpack_from('<I',a,52)[0]
  if str(fab) in S['fab']:instances.append((fab,r,'placed'))
 for ii,(fab,r,group) in enumerate(instances):
  mid,ai=struct.unpack_from('<II',r,64)
  if mid not in mats:continue
  sphere=np.array(struct.unpack_from('<4f',r));lo=np.floor((sphere[:2]-sphere[3])/6400).astype(int);hi=np.floor((sphere[:2]+sphere[3])/6400).astype(int)
  if not any(lo[0]<=x<=hi[0] and lo[1]<=y<=hi[1] for x,y in cells):continue
  if fab not in cache:
   f=find(str(fab)+'.fab_visual_data_streamable_bin')
   if not f:cache[fab]=None
   else:
    try:cache[fab]=(amalur_mesh.parse_file(f),f.read_bytes(),str(f.relative_to(P)))
    except Exception:cache[fab]=None
  if cache[fab] is None:counts['missingmesh']+=1;continue
  mesh,src,srcpath=cache[fab]
  if ai>=len(mesh['assemblies']):counts['badassembly']+=1;continue
  asm=mesh['assemblies'][ai];vb=mesh['vertex_buffers'][asm['vertex_buffer']];stride=vb['stride_bytes'];base=vb['data_file_offset'];nv=vb['vertex_count']
  if stride not in [48,56]:counts['unsupported_stride_'+str(stride)]+=1;continue
  ix=np.array(mesh['index_buffers'][asm['index_buffer']]['indices'],np.int64).reshape(-1,3);xyz=np.array(vb['positions'],np.float64);t=np.array(struct.unpack_from('<3f',r,16));q=struct.unpack_from('<4f',r,32);sc=np.array(struct.unpack_from('<3f',r,48));cq=(-q[0],-q[1],-q[2],q[3]);centerlocal=qr(q,(sphere[:3]-t)[None,:])[0];world=qr(cq,centerlocal+(xyz-centerlocal)*sc)+t
  reach=np.sqrt(((world[np.unique(ix)]-sphere[:3])**2).sum(1)).max()
  if sphere[3]<=0 or reach>sphere[3]*1.25+60:counts['sphere_rejected']+=1;continue
  tri=world[ix];cent=tri.mean(1);cell=np.floor(cent[:,:2]/6400).astype(int);sel=np.array([tuple(c) in cells for c in cell]);ix=ix[sel];tri=tri[sel]
  if not len(ix):continue
  uv0=np.ndarray((nv,2),'<f4',src,base+12,(stride,4));uv1=np.ndarray((nv,2),'<f4',src,base+20,(stride,4)) if stride==56 else uv0;no=20 if stride==48 else 28;frame=[];safe=np.where(abs(sc)>1e-4,sc,1)
  for off in [no,no+8,no+16]:
   vec=np.ndarray((nv,3),'<i2',src,base+off,(stride,2)).astype(np.float64);vec/=safe;vec/=np.maximum(np.linalg.norm(vec,axis=1,keepdims=True),1e-9);frame.append(qr(cq,vec))
  color=np.ndarray((nv,4),'u1',src,base+stride-4,(stride,1));V=np.concatenate([world,frame[0],frame[1],frame[2],uv0,uv1],1).astype('<f4')[ix].reshape(-1,16);C=color[ix].reshape(-1,4).copy();chunks.append((V,C,mid));prov.append(dict(space=int(sid),space_name=sname,instance=ii,group=group,fab=fab,fab_name=S['fab'][str(fab)],assembly=ai,material=mid,material_name=mats[mid]['name'],shader=mats[mid]['shader'],stride=stride,triangles=len(ix),mesh_path=srcpath,mesh_sha256=mesh['input_sha256'],render_record_hex=r.hex(),color_min=C.min(0).tolist(),color_max=C.max(0).tolist()));counts['instances']+=1;counts['triangles']+=len(ix)
 print(sname,dict(counts),'seconds',round(time.time()-start,1),flush=True)
V=np.concatenate([c[0] for c in chunks]);C=np.concatenate([c[1] for c in chunks]);M=np.concatenate([np.full(len(c[0]),c[2],'<u4') for c in chunks]);flags=np.full(len(M),3,'<u4');dtype=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')]);data=np.empty(len(M),dtype);data['v']=V;data['rgba']=C;data['material']=M;data['flags']=flags;assert dtype.itemsize==76
blob=struct.pack('<4s4I',b'OAWT',1,76,len(M),0)+data.tobytes();(OUT/'static-source-attributes.oawt').write_bytes(blob);(OUT/'source-provenance.json').write_text(json.dumps(prov,indent=2));(OUT/'native-materials.json').write_text(json.dumps({str(m):mats[m] for m in set(M.tolist())},indent=2));meta=dict(counts=dict(counts),cells=sorted(cells),bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),header='OAWT u32version1,u32stride76,u32vertexCount,u32indexCount0; triangle soup',vertex='16float32 = pos3,N3,T3,B3,UV0_2,UV1_2;RGBA8;u32nativeMaterialId;u32flags',limitations=['source-correlated current-generation pose recipe, not native nonunit bind proof','singleUV source48 duplicatesUV0 toUV1; flag presently3 means sourceframe+RGBA present, not secondUV observed','only cached source files; no extraction or oldfilewrites','source-triangle soup still needs exact existingcell join beforedeployment','LOD1/2clusterattributeownership not recovered']);(OUT/'attributes-manifest.json').write_text(json.dumps(meta,indent=2));print(meta)
