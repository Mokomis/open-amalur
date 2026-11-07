from pathlib import Path
# Reuse exact sampler/wind/reference/orthographic-ray setup from private grass pick.
p=Path(__file__).resolve().parent
s=(p/'pick_current_grass_shadow.py').read_text();exec(compile(s[:s.index('for cx,cy,dist,possible in cells:')],str(p/'pick_current_grass_shadow.py'),'exec'))
DT76=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')]);DT28=np.dtype([('p','<f4',(3,)),('n','<i2',(4,)),('uv','<f4',(2,))])
cells={}
for k in range(cn):
 cx,cy,*z=struct.unpack_from('<ii6f4I',ib,20+k*48);cells[(cx,cy)]={'lo':np.array(z[:3]),'hi':np.array(z[3:6]),'blo':np.array(z[:3]),'bhi':np.array(z[3:6]),'tris':z[6:9]}
reg=(W/'region-index.bin').read_bytes();rs=struct.unpack_from('<f',reg,16)[0]
for k in range(struct.unpack_from('<I',reg,8)[0]):
 cx,cy,tris,runs,*bounds=struct.unpack_from('<iiII6f',reg,24+k*40);lo=np.array(bounds[:3]);hi=np.array(bounds[3:]);c=cells.setdefault((cx,cy),{'lo':lo.copy(),'hi':hi.copy(),'blo':lo.copy(),'bhi':hi.copy(),'tris':[0,0,0]});c['lo']=np.minimum(c['lo'],lo);c['hi']=np.maximum(c['hi'],hi);c['region_tris']=tris
leaf=(W/'leaf-index.bin').read_bytes();ln,lm=struct.unpack_from('<II',leaf,8);leafmats=set();leafcells=set()
for k in range(lm):leafmats.update(struct.unpack_from('<II',leaf,20+k*8))
for k in range(ln):cx,cy,ntri=struct.unpack_from('<iiI',leaf,20+lm*8+k*12);leafcells.add((cx,cy))
def possible_box(lo,hi):
 out=[]
 for a,d in rays:
  den=np.where(abs(d)>1e-15,d,1e-15);s=(lo-a)/den;t=(hi-a)/den;out.append(np.minimum(s,t).max()<=np.maximum(s,t).min() and np.maximum(s,t).min()>=0)
 return out
packs=[]
for (cx,cy),c in cells.items():
 dist=float(np.linalg.norm(np.maximum(c['blo'][:2]-eye[:2],np.maximum(eye[:2]-c['bhi'][:2],0))));rd=float(np.linalg.norm(np.maximum(c['lo'][:2]-eye[:2],np.maximum(eye[:2]-c['hi'][:2],0))));lod=0 if dist<12800 else 1 if dist<25600 else 2 if dist<100000 else -1;possible=possible_box(c['lo'],c['hi'])
 if not any(possible):continue
 base=lod>=0 and c['tris'][lod]>0;region=rd<100000 and c.get('region_tris',0)>0
 if not(base or region):continue
 lf=(cx,cy) in leafcells and lod>=0
 if base:packs.append((W/f'c{cx}_{cy}_{lod}.bin','base',cx,cy,possible,lf,dist))
 if lf:packs.append((W/f'l{cx}_{cy}.bin','leaf',cx,cy,possible,lf,dist))
 if region:packs.append((W/f'r{cx}_{cy}.bin','region',cx,cy,possible,lf,dist))
print('candidatePacks',len(packs),flush=True)
palette=np.array([.7793933749198914,.08575710654258728,.9925394058227539,.5854730606079102,.7862923741340637,.9102197885513306,.9908282160758972,.5957845449447632,.07477909326553345,.7626959681510925,0,0],np.float32);hits=[[] for _ in pts];scanned=[]
for file,kind,cx,cy,possible,lf,dist in packs:
 if not file.exists():continue
 b=file.read_bytes();ranges=None
 if b[:8]==b'OARGEO1\0':
  _,nv,ni,nd,vs,rr=struct.unpack_from('<8s5I',b);assert vs==76 and rr==48;off=28+48*nd;stride=76;V=np.frombuffer(b,DT76,nv,off);draws=[struct.unpack_from('<4I6fIf',b,28+k*48) for k in range(nd)];ranges=draws
 else:
  magic,nv,ni,nd=struct.unpack_from('<4s3I',b);assert magic in [b'OAWE',b'OAWC'];stride=76 if magic==b'OAWE' else 28;off=16+12*nd;V=np.frombuffer(b,DT76 if stride==76 else DT28,nv,off);draws=[struct.unpack_from('<3I',b,16+k*12) for k in range(nd)]
 pos=(V['v'][:,:3] if stride==76 else V['p']).astype(float);UV=V['v'][:,12:14] if stride==76 else V['uv'];I=np.frombuffer(b,'<u4',ni,off+nv*stride).reshape(-1,3);tm=np.zeros(ni//3,'<u4');run=np.zeros(ni//3,'<u4');allow=np.zeros(ni//3,bool)
 for j,row in enumerate(draws):
  mat,f,n=row[:3];flags=struct.unpack_from('<I',mb,4+mat*28)[0];tm[f//3:(f+n)//3]=mat;run[f//3:(f+n)//3]=j
  if flags&56:continue
  if kind=='base' and lf and mat in leafmats:continue
  if kind=='leaf' and not(flags&2):continue
  if ranges is not None:
   mins,maxs=row[4:6];sph=np.array(row[6:9]);scale=row[11] if row[11]>0 else rs;d2=float(np.sum((eye-sph)**2))*scale*scale
   if d2<mins or d2>=maxs:continue
  allow[f//3:(f+n)//3]=True
  if stride==76:
   prof=struct.unpack_from('<9I12f',nb,12+mat*84)
   if prof[0]==6 and prof[14]!=0:
    ids=np.unique(I[f//3:(f+n)//3]);half=V['v'][ids,14:16].copy().view('<f2').reshape(-1,4).astype(np.float32);phase=half[:,3].astype(int);pos[ids]=(V['v'][ids,:3]+half[:,:3]*(np.float32(prof[14])*palette[phase,None])).astype(np.float32).astype(float)
 if not allow.any():continue
 tri=pos[I];e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0]
 for ri,(a,d) in enumerate(rays):
  if not possible[ri]:continue
  pp=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,pp);valid=(abs(det)>1e-10)&allow;inv=np.divide(1,det,out=np.zeros_like(det),where=valid);tv=a-tri[:,0];u=np.einsum('ij,ij->i',tv,pp)*inv;q=np.cross(tv,e1);v=q@d*inv;t=np.einsum('ij,ij->i',e2,q)*inv;ok=valid&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(t>0)
  for k in np.flatnonzero(ok):
   bary=np.array([1-u[k]-v[k],u[k],v[k]]);pt=bary@tri[k];clip=vp@np.r_[pt,1];z=float(clip[2]/clip[3])
   if not -1<=z<=1:continue
   mat=int(tm[k]);prof=struct.unpack_from('<9I12f',nb,12+mat*84);flags=struct.unpack_from('<I',mb,4+mat*28)[0];cut=(flags>>8&255)/255;clips=np.c_[tri[k],np.ones(3)]@vp.T;screen=(clips[:,:2]/clips[:,3,None]+1)*512;base=np.stack([screen[1]-screen[0],screen[2]-screen[0]],1);area=float(np.linalg.det(base));culled=area>0 and not(flags&0x08000000) and prof[0]!=6;der=np.linalg.inv(base);dl=np.vstack([-der.sum(0),der]);uv=bary@UV[I[k]];grad=(UV[I[k]].T@dl).T;alpha=None;coverage=1.
   if flags&2:
    ids=prof[1:9] if prof[0]>0 else struct.unpack_from('<6I',mb,4+mat*28+4);tid=ids[6] if flags&0x20000000 else ids[2] if prof[0] in [5,6] else ids[0];alpha=sample(tid,uv,grad);coverage=alpha['rgba'][1 if flags&0x20000000 or prof[0] in [5,6] else 3];alpha['texture']=tid
   row={'file':file.name,'kind':kind,'cell':[cx,cy],'lod':(0 if dist<12800 else 1 if dist<25600 else 2) if kind=='base' else None,'triangle':int(k),'indices':I[k].tolist(),'material':mat,'family':prof[0],'flags':flags,'world':pt.tolist(),'D16_float':(z*.5+.5)*65535,'D16_round':round((z*.5+.5)*65535),'uv':uv.tolist(),'uv_gradients':grad.tolist(),'bary':bary.tolist(),'signed_area_GL':area,'culled':bool(culled),'coverage':coverage,'cutoff':cut,'alpha_sample':alpha,'passes':not culled and coverage>=cut,'positions':tri[k].tolist(),'base_positions':(V['v'][I[k],:3] if stride==76 else V['p'][I[k]]).tolist(),'range':list(draws[int(run[k])]) if ranges is not None else None,'file_sha256':hashlib.sha256(b).hexdigest()}
   if stride==76:row.update(native_material_fields=V['material'][I[k]].tolist(),vertex_rgba=V['rgba'][I[k]].tolist())
   hits[ri].append(row)
 scanned.append({'file':file.name,'triangles':len(I),'allowed':int(allow.sum())})
out={'current_middle_VP':vp.tolist(),'points':[],'candidate_packs':len(packs),'scanned':scanned,'scope':'CPU expectedfullyloaded maincamera cLOD selection/l/r authoredranges, frozenleafpalette, CW/back orfamily6two-sided culling, isotropictrilinear alpha; terrainselector notsimulated ifterrain frontcandidate.'}
for pt,rows in zip(pts,hits):
 rows.sort(key=lambda a:a['D16_float']);front=next((x for x in rows if x['passes']),None);out['points'].append({'GL_texel':pt,'first_hit':front,'hits':rows[:60]});print('POINT',pt,'FRONT',None if front is None else {k:front[k] for k in ['file','kind','triangle','material','family','D16_float','coverage','cutoff','world','range']},flush=True)
(O/'current-general-shadow-pick.json').write_text(json.dumps(out,indent=2)+'\n')
