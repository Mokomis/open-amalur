from pathlib import Path
import numpy as np,json,struct,math,hashlib
R=Path(r'C:\Users\rwill\Documents\Opem Amalur');W=R/'work/v40-windows-host/assets/world';O=R/'work/v45-foliage-coverage/image-band-audit/shadow-rock-audit';O.mkdir(exist_ok=True)
vp=np.array(INPUT['vp'],np.float32).astype(float);ivp=np.linalg.inv(vp);eye=np.array(INPUT['eye']);pts=[(911,604),(912,604),(911,605),(912,605),(903,606),(904,606),(903,607),(904,607)]
rays=[]
for x,y in pts:
 a=ivp@np.array([(x+.5)/512-1,(y+.5)/512-1,-1,1]);b=ivp@np.array([(x+.5)/512-1,(y+.5)/512-1,1,1]);a=a[:3]/a[3];b=b[:3]/b[3];d=b-a;d/=np.linalg.norm(d);rays.append((a,d))
ib=(W/'index.bin').read_bytes();cn=struct.unpack_from('<I',ib,8)[0];cells=[]
for k in range(cn):
 cx,cy,*z=struct.unpack_from('<ii6f4I',ib,20+k*48);lo=np.array(z[:3]);hi=np.array(z[3:6]);dist=np.linalg.norm(np.maximum(lo[:2]-eye[:2],np.maximum(eye[:2]-hi[:2],0)))
 if dist>=7000 or z[9]==0:continue
 possible=[]
 for a,d in rays:
  ss=(lo-a)/np.where(abs(d)>1e-15,d,1e-15);tt=(hi-a)/np.where(abs(d)>1e-15,d,1e-15);possible.append(np.maximum(np.minimum(ss,tt).max(),0)<=np.maximum(ss,tt).min())
 if any(possible):cells.append((cx,cy,float(dist),possible))
print('candidateGrassCells',len(cells),flush=True)
wind=np.fromfile(W/'wind.bin','<f4').reshape(64,4);DT=np.dtype([('p','<f4',(3,)),('PW','<u4'),('uv','<f4',(2,)),('n','<f4',(3,)),('c','u1',(4,))]);hits=[[] for p in pts]
texcache={}
def tex(t):
 if t not in texcache:
  b=(W/f't{t}.bin').read_bytes();_,fmt,w,h,n=struct.unpack_from('<4s4I',b);assert fmt==0x8058;at=20;lev=[]
  for _ in range(n):
   size=struct.unpack_from('<I',b,at)[0];at+=4;lev.append(np.frombuffer(b,'u1',size,at).reshape(h,w,4));at+=size;w=max(w//2,1);h=max(h//2,1)
  texcache[t]=lev
 return texcache[t]
def sample(t,uv,grad):
 lev=tex(t);h,w,_=lev[0].shape;gg=grad*[w,h];lod=max(0,min(len(lev)-1,math.log2(max(np.linalg.norm(gg[0]),np.linalg.norm(gg[1]),1e-20))))
 def one(im):
  h,w,_=im.shape;x,y=np.array(uv)*[w,h]-.5;ix,iy=math.floor(x),math.floor(y);a,b=x-ix,y-iy
  return ((im[iy%h,ix%w]*(1-a)+im[iy%h,(ix+1)%w]*a)*(1-b)+(im[(iy+1)%h,ix%w]*(1-a)+im[(iy+1)%h,(ix+1)%w]*a)*b)/255
 l=int(lod);v=one(lev[l])*(1-(lod-l))+one(lev[min(l+1,len(lev)-1)])*(lod-l);return {'lod':lod,'rgba':v.tolist()}
mb=(W/'materials.bin').read_bytes();nb=(W/'native-materials.bin').read_bytes()
for cx,cy,dist,possible in cells:
 f=W/f'g{cx}_{cy}.bin'
 if not f.exists():continue
 b=f.read_bytes();magic,nv,ni,nd=struct.unpack_from('<4s3I',b);assert magic==b'OAWF';off=16+12*nd;V=np.frombuffer(b,DT,nv,off);pos=(V['p']+wind[V['PW']&255,:3]).astype(np.float32).astype(float);I=np.frombuffer(b,'<u4',ni,off+nv*40).reshape(-1,3);tm=np.empty(ni//3,'<u4')
 for j in range(nd):
  mat,first,count=struct.unpack_from('<3I',b,16+j*12);tm[first//3:(first+count)//3]=mat
 tri=pos[I];e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0]
 for ri,(a,d) in enumerate(rays):
  if not possible[ri]:continue
  p=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,p);valid=abs(det)>1e-10;inv=np.divide(1,det,out=np.zeros_like(det),where=valid);tv=a-tri[:,0];u=np.einsum('ij,ij->i',tv,p)*inv;q=np.cross(tv,e1);v=q@d*inv;t=np.einsum('ij,ij->i',e2,q)*inv;ok=valid&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(t>0)
  for k in np.flatnonzero(ok):
   bary=np.array([1-u[k]-v[k],u[k],v[k]]);pt=bary@tri[k];clip=vp@np.r_[pt,1];z=clip[2]/clip[3]
   if not -1<=z<=1:continue
   mat=int(tm[k]);prof=struct.unpack_from('<9I12f',nb,12+mat*84);flags=struct.unpack_from('<I',mb,4+mat*28)[0];cut=(flags>>8&255)/255
   clips=np.c_[tri[k],np.ones(3)]@vp.T;screen=(clips[:,:2]/clips[:,3,None]+1)*512;base=np.stack([screen[1]-screen[0],screen[2]-screen[0]],1);der=np.linalg.inv(base);dl=np.vstack([-der.sum(0),der]);uv=bary@V['uv'][I[k]];grad=(V['uv'][I[k]].T@dl).T;wvgrad=(tri[k][:,:2].T@dl).T
   coverage=sample(prof[3],uv,grad);noise=sample(prof[8],pt[:2]*.02,wvgrad*.02);rb=int((int(V['PW'][I[k,-1]])>>8)&255);rb=rb-256 if rb>=128 else rb
   dd=np.linalg.norm(pt[:2]-eye[:2])-rb*1500*(.5/255);keep=1-min(1,max(0,.0006666666595265*dd-2.33333325386));keep=keep*(1-noise['rgba'][1]*keep)+keep*noise['rgba'][1];alpha=coverage['rgba'][1]*keep
   row={'file':f.name,'cell':[cx,cy],'triangle':int(k),'indices':I[k].tolist(),'material':mat,'family':prof[0],'world':pt.tolist(),'D16_float':(z*.5+.5)*65535,'D16_round':round((z*.5+.5)*65535),'uv':uv.tolist(),'bary':bary.tolist(),'UV_gradients':grad.tolist(),'alpha_texture':prof[3],'alpha_sample':coverage,'noise_texture':prof[8],'noise_sample':noise,'keep':keep,'alpha':alpha,'cutoff':cut,'passes':alpha>=cut,'PW':V['PW'][I[k]].tolist(),'source_base_positions':V['p'][I[k]].tolist(),'displaced_positions':tri[k].tolist(),'file_sha256':hashlib.sha256(b).hexdigest()}
   hits[ri].append(row)
out={'current_middle_VP':vp.tolist(),'points':[],'candidate_grass_cells':len(cells),'wind_sha256':hashlib.sha256((W/'wind.bin').read_bytes()).hexdigest(),'scope':'Expected fullyloaded currentgfiles within7000 mainXYcellrange, exactfrozenwind, nativegrass shadercoverage; isotropictrilinearCPUalpha.'}
for pt,rows in zip(pts,hits):
 rows.sort(key=lambda a:a['D16_float']);front=next((x for x in rows if x['passes']),None);out['points'].append({'GL_texel':pt,'first_grass':front,'hits':rows[:20]});print('POINT',pt,'FRONT',None if front is None else {k:front[k] for k in ['file','triangle','D16_float','alpha','cutoff','world']},flush=True)
(O/'current-grass-shadow-pick.json').write_text(json.dumps(out,indent=2)+'\n')
