"""CPU coverage estimate for one reported opening pixel; no GPU/replay."""
from pathlib import Path
import json,struct,math
import numpy as np
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent;W=P/'work/v40-windows-host/assets/world';report=json.loads((Q/'sky-opening-reverse-coverage.json').read_text());vp=np.array(report['camera']['mvp_column_major']).reshape(4,4,order='F');pixel=np.array([980.5,100.5]);width,height=1536,864
mb=(W/'materials.bin').read_bytes();nb=(W/'native-materials.bin').read_bytes();texcache={};hits=[]
def tex(tid):
 if tid not in texcache:
  b=(W/f't{tid}.bin').read_bytes();_,fmt,w,h,n=struct.unpack_from('<4s4I',b);assert fmt==0x8058;at=20;levels=[]
  for _ in range(n):
   size=struct.unpack_from('<I',b,at)[0];at+=4;levels.append(np.frombuffer(b,'u1',size,at).reshape(h,w,4));at+=size;w=max(1,w//2);h=max(1,h//2)
  texcache[tid]=levels
 return texcache[tid]
def sample(tid,uv,g):
 levels=tex(tid);h,w,_=levels[0].shape;gg=g*[w,h];lod=max(0,min(len(levels)-1,math.log2(max(np.linalg.norm(gg[0]),np.linalg.norm(gg[1]),1e-20))))
 def one(im):
  h,w,_=im.shape;x,y=uv*[w,h]-.5;ix,iy=math.floor(x),math.floor(y);a,b=x-ix,y-iy
  return ((im[iy%h,ix%w]*(1-a)+im[iy%h,(ix+1)%w]*a)*(1-b)+(im[(iy+1)%h,ix%w]*(1-a)+im[(iy+1)%h,(ix+1)%w]*a)*b)/255
 l=int(lod);v=one(levels[l])*(1-(lod-l))+one(levels[min(l+1,len(levels)-1)])*(lod-l);return dict(lod=lod,rgba=v.tolist())
for source in report['rows']:
 si=source['source_index'];mat=source['material_row'];flags,*ts=struct.unpack_from('<7I',mb,4+28*mat);profile=struct.unpack_from('<9I12f',nb,12+84*mat);ts=list(profile[1:9]);family=profile[0];cut=(flags>>8&255)/255
 for fn in source['cells']:
  b=(Q/'candidate-world-full'/fn).read_bytes();_,nv,ni,nd,_,_=struct.unpack_from('<8s5I',b);v=np.ndarray((nv,16),'<f4',b,28+48*nd,(76,4));ix=np.frombuffer(b,'<u4',ni,28+48*nd+76*nv)
  for j in range(nd):
   row=struct.unpack_from('<4I6fIf',b,28+48*j)
   if row[-2]!=si:continue
   triix=ix[row[1]:row[1]+row[2]].reshape(-1,3)
   for triindices in triix:
    pos=v[triindices,:3].astype(float);uvs=v[triindices,12:14].astype(float);clip=np.c_[pos,np.ones(3)]@vp.T
    if np.any(clip[:,3]<=0):continue
    screen=np.c_[(clip[:,0]/clip[:,3]+1)*width*.5,(1-clip[:,1]/clip[:,3])*height*.5];m=np.stack([screen[1]-screen[0],screen[2]-screen[0]],1);det=np.linalg.det(m)
    if abs(det)<1e-9:continue
    der=np.linalg.inv(m);st=der@(pixel-screen[0]);lam=np.r_[1-st.sum(),st]
    if np.any(lam< -1e-8):continue
    iw=1/clip[:,3];den=lam@iw;bary=lam*iw/den;uv=bary@uvs;num=(lam*iw)@uvs;dl=np.vstack([-der.sum(0),der]);grad=np.empty((2,2))
    for axis in range(2):grad[axis]=((dl[:,axis]*iw)@uvs*den-num*(dl[:,axis]@iw))/(den*den)
    tid=ts[2] if family==6 else ts[6] if flags&0x20000000 else ts[0];sampled=sample(tid,uv,grad);green=sampled['rgba'][1] if family==6 or flags&0x20000000 else sampled['rgba'][3]
    hits.append(dict(source_index=si,fab=source['fab'],assembly=source['assembly'],material=mat,family=family,raw_alpha_texture=tid,uv=uv.tolist(),uv_gradients=grad.tolist(),coverage_sample=sampled,cutoff=cut,passes_alpha=green>=cut,clip_w=float(1/den),depth_ndc=float(lam@(clip[:,2]/clip[:,3])),screen_signed_area=det,world=(bary@pos).tolist()))
hits.sort(key=lambda h:h['clip_w']);out=dict(pixel=[980,100],scope='Existing9regionalprojectioncandidates only; perspectiveUV +isotropicbilinear/trilinearestimate, noGPU/replay; edgequad/derivative differences remain',hits=hits)
(Q/'sky-opening-980-100-source-coverage.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
