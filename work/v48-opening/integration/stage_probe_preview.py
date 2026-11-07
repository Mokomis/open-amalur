from pathlib import Path
import sys,json,struct,hashlib,collections,shutil
import numpy as np
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[3];Q=P/'work/v48-opening/content-audit';C=Q/'candidate-first-room';O=P/'work/v48-opening/integration/probe-preview';W=O/'world';W.mkdir(parents=True,exist_ok=True)
NONE=0xffffffff
DT=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('mid','<u4'),('flags','<u4')])
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 sources=json.loads((Q/'1417252-source-render-records.json').read_text());byid={r['source_index']:r for r in sources}
 contracts=json.loads((Q/'first-room-material-contracts.json').read_text())['materials'];supported=[m for m in contracts if m['candidate_existing_family'] or m['material'] in [464114,469438]]
 texturemanifest=json.loads((C/'texture-stage-manifest.json').read_text());tex={r['asset']:r for r in texturemanifest['textures']}
 # Only exact implemented families1/3/4, source slots and scalar parameters.
 profiles=[];need=set()
 for m in supported:
  family=m['candidate_existing_family'] or 11;src={r['slot']:r['asset'] for r in m['texture_slots']}
  assert m['cull'] in [0,2]
  assets=[src.get(k) or None for k in [0,3,2,8,11,10,1]]+[None]
  if family==1:assets[3:6]=[None,None,None]
  if family==11:assets=[src.get(k) or None for k in [0,3,2,1]]+[None]*4
  if family!=4 and not m['alpha_test']:assets[6]=None
  for a in assets:
   if a is not None:assert a in tex,(m['material'],a);need.add(a)
  params={p['name']:p['values'] for p in m['parameters']};color=params.get('ConstantColor',[0.0]*4);spec=params['SpecularValues'];uv=[params.get(n,[1.0])[0] for n in ['UTile','VTile','UTile2','VTile2']]
  if family==11:
   assert not m['alpha_test'] and params.get('Opacity',[1.0])[0]==1.0
   color=params['TintColor'];uv=[1.0,1.0,params['ReflectionInfluence'][0],0.0]
  flags=(2 if m['alpha_test'] else 0)|(m['cutoff_byte']<<8)|(0x10000000 if m['cull']==2 else 0x08000000)
  if m['alpha_test']:assert family==1 and assets[6] is not None;flags|=0x20000000
  profiles.append(dict(local_material=len(profiles),native_material=m['material'],shader=m['shader_name'],family=family,source_cull=m['cull'],alpha_test=m['alpha_test'],cutoff=m['cutoff_byte'],flags=flags,assets=assets,color=color,specular=spec,uv=uv))
 tids={a:i for i,a in enumerate(sorted(need))};mid={r['native_material']:r['local_material'] for r in profiles};mb=[];nb=[]
 for p in profiles:
  slots=[tids[a] if a is not None else NONE for a in p['assets']];p['texture_slots']=slots
  mb.append(struct.pack('<7I',p['flags'],*slots[:6]));nb.append(struct.pack('<9I12f',p['family'],*slots,*p['color'],*p['specular'],*p['uv']))
 bank=struct.pack('<I',len(profiles))+b''.join(mb);native=struct.pack('<8sI',b'OANM001\0',len(profiles))+b''.join(nb);(W/'materials.bin').write_bytes(bank);(W/'native-materials.bin').write_bytes(native)
 texturefiles=[]
 for a,i in sorted(tids.items(),key=lambda x:x[1]):
  r=tex[a];b=(C/r['portable_file']).read_bytes();assert sha(b)==r['portable_sha256'];(W/f't{i}.bin').write_bytes(b);texturefiles.append(dict(texture=i,asset=a,file=f't{i}.bin',bytes=len(b),sha256=sha(b),source_first_mip=r['portable_source_first_mip'],width=r['portable_width'],height=r['portable_height'],mips=len(r['portable_levels'])))
 excluded=[];allowed=set()
 for r in sources:
  if r['material'] not in mid:reason='unsupported_shader_family'
  elif any(abs(s-1.0)>1e-6 for s in r['scale']):reason='quarantined_nonunit_transform'
  else:allowed.add(r['source_index']);continue
  excluded.append(dict(source_index=r['source_index'],fab=r['fab'],assembly=r['assembly'],material=r['material'],scale=r['scale'],reason=reason))
 registry=[];cells=[];storedtri=0;alltri=0;removedtri=collections.Counter();ranges=0
 for f in sorted((C/'world').glob('r*_*.bin')):
  b=f.read_bytes();magic,nv,ni,nd,vs,rs=struct.unpack_from('<8s5I',b);assert (magic,vs,rs)==(b'OARGEO1\0',76,48);va=28+nd*48;ia=va+nv*76;V=np.frombuffer(b,DT,nv,va);I=np.frombuffer(b,'<u4',ni,ia)
  keep=[]
  for j in range(nd):
   r=list(struct.unpack_from('<4I6fIf',b,28+j*48));sid=r[10]
   if sid in allowed:keep.append(r)
   else:removedtri['unsupported_shader_family' if byid[sid]['material'] not in mid else 'quarantined_nonunit_transform']+=r[2]//3
  if not keep:continue
  blocks=[];reuse={};newruns=[];nidx=0
  for r in keep:
   k=(r[1],r[2])
   if k not in reuse:reuse[k]=nidx;blocks.append(I[r[1]:r[1]+r[2]]);nidx+=r[2]
   newr=r.copy();newr[0]=mid[byid[r[10]]['material']];newr[1]=reuse[k];newruns.append(newr);alltri+=r[2]//3
  oldidx=np.concatenate(blocks);used,inv=np.unique(oldidx,return_inverse=True);newv=V[used].copy();newi=inv.astype('<u4');assert newv['mid'].max() in mid
  rb=b''.join(struct.pack('<4I6fIf',*r) for r in newruns);out=struct.pack('<8s5I',magic,len(newv),len(newi),len(newruns),76,48)+rb+newv.tobytes()+newi.tobytes()
  for oldr,newr in zip(keep,newruns):
   old=V[I[oldr[1]:oldr[1]+oldr[2]]];new=newv[newi[newr[1]:newr[1]+newr[2]]];assert old.tobytes()==new.tobytes()
  (W/f.name).write_bytes(out);stem=f.stem[1:].split('_');cx,cy=map(int,stem);lo=newv['v'][:,:3].min(0);hi=newv['v'][:,:3].max(0);registry.append(struct.pack('<iiII6f',cx,cy,len(newi)//3,len(newruns),*lo,*hi));cells.append(dict(file=f.name,cell=[cx,cy],bytes=len(out),sha256=sha(out),vertices=len(newv),stored_triangles=len(newi)//3,ranges=len(newruns),bounds=[lo.tolist(),hi.tolist()]));storedtri+=len(newi)//3;ranges+=len(newruns)
 index=struct.pack('<8sIIfI',b'OARGIDX1',len(cells),len(profiles),1.0,0)+b''.join(registry);(W/'region-index.bin').write_bytes(index)
 # Actual collision andregioncellbounds formemptybaseentries, no c-filesrequested.
 bounds={tuple(r['cell']):r['bounds'] for r in cells};collision=[]
 for f in sorted((C/'world').glob('k*_*.bin')):
  b=f.read_bytes();n=struct.unpack_from('<I',b)[0];T=np.frombuffer(b,'<f4',n*9,4).reshape(-1,3);xy=tuple(map(int,f.stem[1:].split('_')));lo,hi=T.min(0),T.max(0)
  if xy in bounds:bounds[xy]=[np.minimum(bounds[xy][0],lo).tolist(),np.maximum(bounds[xy][1],hi).tolist()]
  else:bounds[xy]=[lo.tolist(),hi.tolist()]
  (W/f.name).write_bytes(b);collision.append(dict(file=f.name,triangles=n,sha256=sha(b)))
 base= b'OAWI'+struct.pack('<fIII',6400.,len(bounds),len(tids),0)+b''.join(struct.pack('<ii6f4I',*xy,*bb[0],*bb[1],0,0,0,0) for xy,bb in sorted(bounds.items()));(W/'index.bin').write_bytes(base)
 # No fabricated OALG globals. Keepauthoredsourceenvironment separate forrootreader.
 env=O/'environment';env.mkdir(exist_ok=True)
 for f in (C/'environment').iterdir():
  if f.is_file():shutil.copyfile(f,env/f.name)
 report=dict(status='Reader-format portable preview staged; noGPUloadperformed; sourceenvironmentintegrationrequired',space=1417252,region=1262814,spawn=[4312,2806,-314,-180],source_rows=len(sources),retained_rows=ranges,excluded_rows=len(excluded),excluded_row_counts=dict(collections.Counter(r['reason'] for r in excluded)),excluded_all_range_triangles=dict(removedtri),stored_triangles=storedtri,all_range_triangles=alltri,materials=profiles,textures=texturefiles,material_count=len(profiles),texture_count=len(tids),cells=cells,base_empty_cells=len(bounds),collision=collision,excluded=excluded,formats=dict(index='OAWI20Bheader+48Bemptybasecells; baseLODtri0 no cfilesneeded',region_index='OARGIDX1 24Bheader+40Brows; mc matchesMATS',geometry='OARGEO1 28Bheader+48Branges+OAWE76indexedvertices+u32indices',materials='u32count+28Brows',native_materials='OANM001\\0,u32count+84Brows',textures='OATX RGBA8 allsourceauthoredmipsfromfirst<=512; noresize/generation',collision='kCX_CY.bin:u32tris+float32XYZ*9',lighting='lighting.bin deliberatelyabsent: OALG native_sky/ambientconstants universalitynotproven; neutralglobalsremainunready; rootauthoredsceneenvironmentreaderrequired'),sha256=dict(index=sha(base),region_index=sha(index),materials=sha(bank),native_materials=sha(native)),limits=['Families1/3/4 plus distinct11GlassMetalProbe for exact authored nonzero-probe MIDs464114/469438. Source zero-probe476693 remains excluded. Other families unimplemented.','AllnonunitSPACEtransforms quarantined,notjust51sphereoutliers; no fittedposefix.','Sourcegeometry76B bytes/indextriangleorder identicalforretainedranges; onlylocalmaterialrowmap/headercompaction changes.','Nativequalityglobal4 issharedbinarydefault; neutralregistryDistanceScale1preservesrawsourceintervals forrootchoice.','Rawsourceflagslowerbits preserved; currentgenericreaderdoesnotreproduceallnativeper-pass exclusionmasksemantics.','No dynamicactors/0x98visuals/cinematics/particles/mobsorquestbehaviorbundled inthisstaticpreview.','Environmentbase/start/cinematic XML profilesallpreserved; actualopeningoverridechoiceunproven.','Root scene-profile.bin provides source room environment. Ambient specular globals unknown/explicitly disabled; full lighting parity is not claimed.'])
 (O/'preview-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ['status','retained_rows','excluded_row_counts','excluded_all_range_triangles','stored_triangles','all_range_triangles','material_count','texture_count','base_empty_cells']},indent=2));print('BYTES',sum(f.stat().st_size for f in W.iterdir()))
if __name__=='__main__':main()
