"""Offline ray/UV/material provenance of selected final-r2 pixels; no GPU work."""
from pathlib import Path
import numpy as np,json,struct,hashlib,math
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent
W=P/'work/v40-windows-host/assets/world';meta=json.loads((P/'work/v44-native-fidelity/bridge-native-final-r2.json').read_text())
vp=np.array(meta['mvp_column_major'],np.float64).reshape(4,4,order='F');ivp=np.linalg.inv(vp);eye=np.array(meta['eye']);width=meta['width'];height=meta['height']
pixels=[(980,100)]
DT=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')])
mb=(W/'materials.bin').read_bytes();mc=struct.unpack_from('<I',mb)[0];mats=[struct.unpack_from('<7I',mb,4+i*28) for i in range(mc)]
nb=(W/'native-materials.bin').read_bytes();nc=struct.unpack_from('<I',nb,8)[0];native={}
for i in range(nc):
 row=struct.unpack_from('<9I12f',nb,12+i*84);native[i]=dict(family=row[0],textures=row[1:9],color=row[9:13],spec=row[13:17])
def ray(pixel):
 x,y=pixel;ndc=[2*(x+.5)/width-1,1-2*(y+.5)/height]
 a=ivp@np.array([*ndc,-1,1]);b=ivp@np.array([*ndc,1,1]);a=a[:3]/a[3];b=b[:3]/b[3];d=b-a;d/=np.linalg.norm(d);return a,d
rays=[ray(p) for p in pixels];hits=[[] for p in pixels]
ib=(W/'index.bin').read_bytes();cn=struct.unpack_from('<I',ib,8)[0];cells=[]
for i in range(cn):
 ix,iy,*z=struct.unpack_from('<ii6f4I',ib,20+i*48);lo=np.array(z[:3]);hi=np.array(z[3:6]);d=np.maximum(lo[:2]-eye[:2],np.maximum(eye[:2]-hi[:2],0));dist=float(np.linalg.norm(d));lod=0 if dist<12800 else 1 if dist<25600 else 2 if dist<100000 else -1
 if lod<0:continue
 possible=[]
 for a,v in rays:
  ss=(lo-a)/v;tt=(hi-a)/v;near=float(np.minimum(ss,tt).max());far=float(np.maximum(ss,tt).min());possible.append(far>=max(near,0))
 if any(possible):
  cells.append((ix,iy,lod,dist,possible,False))
  if (W/f'l{ix}_{iy}.bin').exists():cells.append((ix,iy,-1,dist,possible,False))
  if lod>0:cells.append((ix,iy,0,dist,possible,True))
print('ray candidate cells',len(cells),flush=True)
for cx,cy,lod,dist,possible,fine_cutout_only in cells:
 f=W/(f'l{cx}_{cy}.bin' if lod==-1 else f'c{cx}_{cy}_{lod}.bin');b=f.read_bytes();magic,nv,ni,nd=struct.unpack_from('<4s3I',b);off=16+12*nd
 if magic==b'OAWE':
  verts=np.frombuffer(b,DT,nv,off);pos=verts['v'][:,:3].astype(np.float64);uv=verts['v'][:,12:14];stride=76
 else:
  assert magic==b'OAWC';dd=np.dtype([('p','<f4',(3,)),('n','<i2',(4,)),('uv','<f4',(2,))]);verts=np.frombuffer(b,dd,nv,off);pos=verts['p'].astype(np.float64);uv=verts['uv'];stride=28
 ix=np.frombuffer(b,'<u4',ni,off+nv*stride).reshape(-1,3);tm=np.empty(ni//3,np.uint32)
 for n in range(nd):
  mat,first,count=struct.unpack_from('<3I',b,16+n*12);tm[first//3:(first+count)//3]=mat
 # Current reference leaf palette is the original saved twelve scalars.
 palette=np.array([.7793933749198914,.08575710654258728,.9925394058227539,.5854730606079102,.7862923741340637,.9102197885513306,.9908282160758972,.5957845449447632,.07477909326553345,.7626959681510925,0,0])
 if magic==b'OAWE':
  for mat in np.unique(tm):
   n=native.get(int(mat),{})
   if n.get('family')!=6 or n['spec'][1]==0:continue
   ids=np.unique(ix[tm==mat]);packed=verts['v'][ids,14:16].copy().view('<f2').reshape(-1,4).astype(np.float64);phase=packed[:,3].astype(int);assert np.all((phase>=0)&(phase<12));pos[ids]+=packed[:,:3]*(n['spec'][1]*palette[phase,None])
 tri=pos[ix];e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0]
 for r,(a,d) in enumerate(rays):
  if not possible[r]:continue
  p=np.cross(np.broadcast_to(d,e2.shape),e2);det=np.einsum('ij,ij->i',e1,p);valid=abs(det)>1e-10;inv=np.zeros_like(det);inv[valid]=1/det[valid];tv=a-tri[:,0];u=np.einsum('ij,ij->i',tv,p)*inv;q=np.cross(tv,e1);v=q@d*inv;t=np.einsum('ij,ij->i',e2,q)*inv;ok=valid&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(t>0)
  for k in np.flatnonzero(ok):
   material=int(tm[k]);flags=mats[material][0];
   if lod>=0 and material in [0,6,8,293,294,295] and (W/f'l{cx}_{cy}.bin').exists():continue
   is_cutout=bool(flags&2) and not(flags&(1|8|16|32))
   if fine_cutout_only and not is_cutout:continue
   if not fine_cutout_only and lod>0 and is_cutout:continue
   bary=np.array([1-u[k]-v[k],u[k],v[k]]);pt=bary@tri[k];clip=vp@np.r_[pt,1];z=clip[2]/clip[3]
   if z< -1 or z>1:continue
   mat=int(tm[k]);uvs=uv[ix[k]].astype(np.float64);value=bary@uvs
   clips=np.c_[tri[k],np.ones(3)]@vp.T;screen=np.c_[(clips[:,0]/clips[:,3]+1)*width*.5,(1-clips[:,1]/clips[:,3])*height*.5];base=np.stack([screen[1]-screen[0],screen[2]-screen[0]],1);der=np.linalg.inv(base);s=np.array(pixels[r],float)+.5;st=der@(s-screen[0]);lam=np.r_[1-st.sum(),st];dl=np.vstack([-der.sum(0),der]);iw=1/clips[:,3];den=lam@iw;num=(lam*iw)@uvs;grad=np.empty((2,2))
   for axis in range(2):grad[axis]=((dl[:,axis]*iw)@uvs*den-num*(dl[:,axis]@iw))/(den*den)
   row=dict(cell=[cx,cy],lod=lod,cell_distance=dist,file=f.name,magic=magic.decode(),triangle=int(k),index_offset=int(k*3),vertex_indices=ix[k].tolist(),material=mat,family=native.get(mat,{}).get('family',0),distance=float(t[k]),depth_ndc=float(z),depth24=int(round((float(z)*.5+.5)*16777215)),depth24_error_from_observed=int(round((float(z)*.5+.5)*16777215))-16762614,world=pt.tolist(),uv=value.tolist(),uv_gradients=grad.tolist(),det=float(det[k]),barycentric=bary.tolist(),position_triangle=tri[k].tolist(),uv_triangle=uvs.tolist())
   if magic==b'OAWE':row.update(native_material_fields=verts['material'][ix[k]].tolist(),vertex_rgba=verts['rgba'][ix[k]].tolist(),normal_triangle=verts['v'][ix[k],3:6].tolist())
   hits[r].append(row)
 print('cell',cx,cy,lod,'hits',sum(map(len,hits)),flush=True)
texcache={}
def texture(tid):
 if tid not in texcache:
  b=(W/f't{tid}.bin').read_bytes();assert b[:4]==b'OATX';fmt,w,h,n=struct.unpack_from('<4I',b,4);o=20;levels=[]
  for _ in range(n):
   size=struct.unpack_from('<I',b,o)[0];o+=4;levels.append(np.frombuffer(b,'u1',size,o).reshape(h,w,4));o+=size;w=max(w//2,1);h=max(h//2,1)
  texcache[tid]=levels
 return texcache[tid]
def sample(tid,uv,grad):
 levels=texture(tid);h,w,_=levels[0].shape;g=np.array(grad)*[w,h];lod=max(0,min(len(levels)-1,math.log2(max(np.linalg.norm(g[0]),np.linalg.norm(g[1]),1e-20))))
 def bilinear(im):
  h,w,_=im.shape;x,y=np.array(uv)*[w,h]-.5;ix=math.floor(x);iy=math.floor(y);a=x-ix;b=y-iy
  return ((im[iy%h,ix%w]*(1-a)+im[iy%h,(ix+1)%w]*a)*(1-b)+(im[(iy+1)%h,ix%w]*(1-a)+im[(iy+1)%h,(ix+1)%w]*a)*b)/255
 lo=int(lod);hi=min(lo+1,len(levels)-1);v=bilinear(levels[lo])*(1-(lod-lo))+bilinear(levels[hi])*(lod-lo);return dict(lod=lod,rgba=v.tolist())
out=[]
for pixel,rows in zip(pixels,hits):
 rows.sort(key=lambda x:x['distance']);front=None
 for row in rows:
  mat=row['material'];flags,*tid=mats[mat];nat=native.get(mat,{});ts=nat.get('textures',tid) if nat.get('family',0)>0 else tid;cut=((flags>>8)&255)/255;row['flags']=flags;row['cutoff']=cut;row['diffuse_texture']=int(ts[0]);row['diffuse_sample']=sample(int(ts[0]),row['uv'],row['uv_gradients']);color=row['diffuse_sample']['rgba'];coverage=color[3]
  if row['family']==6:
   row['raw_alpha_texture']=int(ts[2]);row['raw_alpha_sample']=sample(int(ts[2]),row['uv'],row['uv_gradients']);coverage=row['raw_alpha_sample']['rgba'][1]
  if flags&0x20000000:
   row['raw_alpha_texture']=int(ts[6]);row['raw_alpha_sample']=sample(int(ts[6]),row['uv'],row['uv_gradients']);coverage=row['raw_alpha_sample']['rgba'][1]
  if mat in [0,6,8]:
   a=679 if mat==0 else 680;row['equivalent_native_alpha_texture']=a;row['equivalent_native_alpha_sample']=sample(a,row['uv'],row['uv_gradients'])
  row['coverage']=coverage;row['passes_current_cutout']=not(flags&2) or coverage>=cut;row['culled_backface']=bool(flags&0x10000000) and not(flags&0x08000000) and row['family']!=6 and row['det']<0
  if row['passes_current_cutout'] and not row['culled_backface'] and front is None:front=row
 out.append(dict(pixel=pixel,first_covered_hit=front,hits=rows[:80],total_hits=len(rows)))
report=dict(camera=meta,cell_lod_policy='finestcutoutsonly;opaque=fullyloaded expectedLOD: XYdistance-to-indexAABB<12800 LOD0,<25600 LOD1,<64000 LOD2; exact runtimeLODnotinstrumented',leaf_wind='referencecapturedpalette appliedtofamily6 movedvertices; noGPUwork',sampler='offline isotropic bilinear/trilinear implicitLOD estimate; legacyanis4notexactlysimulated',pixels=out)
(Q/'current-live-opening-980-100-pick.json').write_text(json.dumps(report,indent=2))
for row in out:
 h=row['first_covered_hit'];print('PIXEL',row['pixel'],'FRONT',None if h is None else {k:h[k] for k in ['cell','lod','material','family','uv','coverage','diffuse_sample']},flush=True)
