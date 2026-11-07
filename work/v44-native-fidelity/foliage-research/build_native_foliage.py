"""Emit only private native foliage overlays. Never mutate active world assets.
Recovered loaders 00d46dd0/00d45f10/00d3ccb0/00d3a810/00d0e2e0;
generator 00d3a350/00d398f0/00d39c80/00d39fd0/00d393e0;
transform 00d2ac40. Static zero-wind geometry; no runtime parity claim.
"""
from pathlib import Path
import collections, hashlib, json, math, struct, zlib
import numpy as np
ROOT=Path.home()/'Documents/Opem Amalur'
OUT=ROOT/'work/v44-native-fidelity/foliage-research'
OUT.mkdir(parents=True,exist_ok=True)
BASE=ROOT/'work/v40-windows-host/assets/world'
DATA=ROOT/'work/v20-inputs/DATA_0.pak'
F32=lambda x:np.asarray(x,dtype=np.float32)
VTX=np.dtype([('p','<f4',3),('wind','<u4'),('t','<f4',2),('n','<f4',3),('color','u1',4)])
assert VTX.itemsize==40
CELLS=sorted({(x,y) for x in [-1,0,1] for y in [-11,-10,-9]}|{(x,y) for x in [0,1,2] for y in [-15,-14,-13]})
ORIGIN=-102425.;TILE=3200.;CELL=6400.
def sha(b):return hashlib.sha256(b).hexdigest()
def read_u(b,o):return struct.unpack_from('<I',b,o)[0]
def parse_terrain(b):
 o=104
 for _ in range(read_u(b,100)):
  n=read_u(b,o);o+=8+(n+7)//8
 start=o;asset,intervals,w,h=struct.unpack_from('<4I',b,o);o+=16
 transform=b[o:o+45];o+=45;dist=struct.unpack_from('<2f',b,o);o+=8;step=struct.unpack_from('<f',b,o)[0];o+=4
 n=read_u(b,o);o+=4;layers=[]
 for li in range(n):
  nd=read_u(b,o);o+=4;defs=[]
  for _ in range(nd):
   ds=o;ng=read_u(b,o);o+=4;geoms=[]
   for _ in range(ng):
    nv=read_u(b,o);o+=4;vo=o;v=np.frombuffer(b,dtype=np.dtype([('p','<f4',3),('uv','<f4',2),('color','<u4')]),count=nv,offset=o).copy();o+=nv*24
    ni=read_u(b,o);o+=4;io=o;idx=np.frombuffer(b,'<u2',ni,o).copy();o+=ni*2
    nn=read_u(b,o);o+=4;no=o;nor=np.frombuffer(b,'<f4',nn*3,o).reshape(-1,3).copy();o+=nn*12
    bounds=struct.unpack_from('<6f',b,o);o+=24;mat=read_u(b,o);o+=4
    assert idx.max()<nv and nn==nv
    geoms.append(dict(v=v,idx=idx,nor=nor,bounds=bounds,material=mat,vertex_offset=vo,index_offset=io,normal_offset=no,vertex_sha256=sha(b[vo:vo+nv*24]),index_sha256=sha(b[io:io+ni*2]),normal_sha256=sha(b[no:no+nn*12])))
   seed,np_=struct.unpack_from('<2I',b,o);o+=8;params=np.frombuffer(b,'<f4',np_,o).copy();o+=np_*4;bounds=struct.unpack_from('<6f',b,o);o+=24
   defs.append(dict(seed=seed,params=params,bounds=bounds,geoms=geoms,offset=ds,end=o))
  layers.append(defs)
 # field148, veggie MultiEntryFile descriptor, RLE tile lookup.
 metadata_end=o;field148=struct.unpack_from('<f',b,o)[0];o+=4;desc=struct.unpack_from('<6I',b,o);o+=24
 n,flag=struct.unpack_from('<2I',b,o);o+=8;A=[]
 while len(A)<n:
  run=read_u(b,o);o+=4
  assert run<=n-len(A)
  if flag:A.extend(struct.unpack_from('<%dI'%run,b,o));o+=run*4
  else:A.extend([None]*run)
  flag=not flag
 assert n==w*h and desc==(1,21,64,8,32768,3) and (intervals,w,h,step)==(64,65,65,50.)
 return layers,A,dict(mesh_start=start,metadata_end=metadata_end,descriptor=desc,rle_end=o,grid=[intervals,w,h,step],field148=field148)
def entry(s,key):
 at=(key&0x1fffff)*64;n=read_u(s,at);assert n==1
 raw,total,zero,raw2,comp=struct.unpack_from('<5I',s,at+4);assert raw==raw2 and zero==0 and comp<=total<=comp+32
 d=zlib.decompress(s[at+24:at+24+comp]);assert len(d)==raw;return d,at
def parse_tile(d):
 o=0;n=read_u(d,o);o+=4;assert n==4225
 H=np.frombuffer(d,'<f4',n,o).reshape(65,65);o+=n*4
 n=read_u(d,o);o+=4;assert n in (0,4225)
 mask=np.frombuffer(d,'u1',n,o).reshape(65,65) if n else np.full((65,65),255,'u1');o+=n
 lo,hi,n=struct.unpack_from('<2fI',d,o);o+=12;layers=[]
 for _ in range(n):
  nn=read_u(d,o);o+=4;assert nn in (0,4225)
  layers.append(np.frombuffer(d,'<f4',nn,o).reshape(65,65) if nn else None);o+=nn*4
 assert len(d)-o in (0,16),(len(d),o)
 return H,mask,layers
# 00cec950 -> 00b3aad0(0)/00b0ab40 is standard MT19937 seed0,
# not NumPy's newer default generator. It fills 1024 complete uint32 values.
SEEDS=np.random.RandomState(0).randint(0,2**32,size=1024,dtype=np.uint32).astype(np.int64)
def lcg(v):return (v*0x343fd+0x269ec3)&0xffffffff
def rnd(v):return F32(((v>>16)&0x7fff)*3.0518509447574615e-5)
def bilinear(a,x,y):
 ix=np.floor(x).astype(int);iy=np.floor(y).astype(int);fx=F32(x-ix);fy=F32(y-iy)
 assert (ix>=0).all() and (iy>=0).all() and (ix<64).all() and (iy<64).all()
 q00=a[iy,ix];q10=a[iy,ix+1];q01=a[iy+1,ix];q11=a[iy+1,ix+1]
 # Native scalar helper retains double intermediates then rounds each row.
 r0=F32(q10.astype('f8')*fx+q00.astype('f8')*(1-fx.astype('f8')))
 r1=F32(q11.astype('f8')*fx+q01.astype('f8')*(1-fx.astype('f8')))
 return F32(r0.astype('f8')*(1-fy.astype('f8'))+r1.astype('f8')*fy)
def generate(tx,ty,H,mask,D,definition):
 pp=definition['params'];p=F32(pp.astype('f8')*0.0010000000474974513)
 density_complement=F32(1.-float(p[1]))
 if float(density_complement)==1:return None
 exponent=F32(2*float(density_complement)-1)
 spacing=F32(float(F32(math.pow(16.,float(exponent))))*100.)
 # The second pow computes 4**(normalized size -1); it is the density
 # acceptance multiplier at context+0x30, not geometric scale.
 acceptance=F32(math.pow(4.,float(F32(float(p[0])-1.))))
 x0,y0=tx*TILE,ty*TILE
 cols=np.arange(int(F32(x0/spacing)),int(F32((x0+TILE)/spacing))+1,dtype=np.int64)
 rows=np.arange(int(F32(y0/spacing)),int(F32((y0+TILE)/spacing))+1,dtype=np.int64)
 xx,yy=np.meshgrid(cols,rows);xx=xx.ravel();yy=yy.ravel()
 state=(SEEDS[((yy&31)<<5)|(xx&31)]+xx*-0x1ed3af7f+yy*-0x4d2fa1ed+definition['seed']*-0x7b8b945d)&0xffffffff
 state=lcg(state);x=F32(F32(rnd(state)+F32(xx))*spacing)
 state=lcg(state);y=F32(F32(rnd(state)+F32(yy))*spacing)
 keep=(x>=x0)&(x<x0+TILE)&(y>=y0)&(y<y0+TILE)
 x=x[keep];y=y[keep];state=state[keep]
 fx=F32((x-x0)*F32(.02));fy=F32((y-y0)*F32(.02));dens=bilinear(D,fx,fy)
 state=lcg(state);keep=rnd(state)<F32(dens*acceptance)
 x=x[keep];y=y[keep];fx=fx[keep];fy=fy[keep];dens=dens[keep];state=state[keep]
 if not len(x):return None
 height=bilinear(H,fx,fy)
 ix=np.floor(fx).astype(int);iy=np.floor(fy).astype(int)
 q00=H[iy,ix];q10=H[iy,ix+1];q01=H[iy+1,ix];q11=H[iy+1,ix+1]
 # 00c7cb90 cross((step,step,q11-q00),(-step,step,q01-q10)).
 tnormal=F32(np.stack([q00-q10+q01-q11,q00+q10-q01-q11,np.full(len(ix),100.)],-1))
 tnormal=F32(tnormal/np.linalg.norm(tnormal,axis=1,keepdims=True))
 shade=bilinear(mask.astype('f4'),fx,fy).astype(np.uint8)
 state=lcg(state);windphase=rnd(state)
 state=lcg(state);windindex=(F32(np.sqrt(F32(np.sqrt(rnd(state)))))*255).astype(np.uint32)
 state=lcg(state);overall=F32(1.-F32(rnd(state)*p[3]))
 state=lcg(state);rz=rnd(state)
 invdensity=F32(1.-dens);combined=F32(1.-(1.-float(p[7]))*(1.-float(p[6])))
 sx=F32((1.-p[6]*invdensity)*overall)
 sz=F32(F32((1.-combined*invdensity)*overall)*F32(1.-rz*p[4]))
 state=lcg(state);yaw=F32(rnd(state)*F32(6.283180236816406))
 state=lcg(state);brightness=F32(1.-rnd(state)*p[2])
 sink=F32(F32(float(p[5])*definition['bounds'][5])*invdensity)
 return dict(x=F32(x+ORIGIN),y=F32(y+ORIGIN),z=F32(height-sink),sx=sx,sz=sz,yaw=yaw,shade=shade,brightness=brightness,windphase=windphase,windindex=windindex,density=dens,terrain_normal=tnormal,normal_blend=float(p[9]),sink=sink,windcurve=float(F32(float(p[8])*9.999999747378752e-5)),spacing=float(spacing),acceptance=float(acceptance))
def main():
 terrain=(DATA/'431658.terrain_bin').read_bytes();stream=(DATA/'431658.veggie_streamable_bin').read_bytes();defs,keys,metadata=parse_terrain(terrain)
 overlay=OUT/'pack-overlay';overlay.mkdir(exist_ok=True)
 src_meta=json.loads((ROOT/'work/v22-stress/zone-dal/zone_materials.json').read_text())
 material_index=src_meta['grass']
 vertices=collections.defaultdict(list);indices=collections.defaultdict(list);instances=[];tiles=[];layercounts=collections.Counter();seed_examples=SEEDS[:8].tolist();
 cellset=set(CELLS)
 txs=range(math.floor((min(x for x,y in CELLS)*CELL-ORIGIN)/TILE),math.floor(((max(x for x,y in CELLS)+1)*CELL-ORIGIN)/TILE)+1)
 tys=range(math.floor((min(y for x,y in CELLS)*CELL-ORIGIN)/TILE),math.floor(((max(y for x,y in CELLS)+1)*CELL-ORIGIN)/TILE)+1)
 for ty in tys:
  for tx in txs:
   if tx<0 or ty<0 or tx>=65 or ty>=65:continue
   # Only touch native tiles that overlap at least one selected cell.
   if not any(tx*TILE+ORIGIN<(cx+1)*CELL and (tx+1)*TILE+ORIGIN>cx*CELL and ty*TILE+ORIGIN<(cy+1)*CELL and (ty+1)*TILE+ORIGIN>cy*CELL for cx,cy in CELLS):continue
   key=keys[ty*65+tx]
   if key is None:continue
   d,at=entry(stream,key);H,mask,layers=parse_tile(d);tiles.append(dict(tile=[tx,ty],key=key,stream_offset=at,sha256=sha(d),density_layers=len(layers)))
   for li,D in enumerate(layers):
    if D is None or not D.any():continue
    for di,de in enumerate(defs[li]):
     inst=generate(tx,ty,H,mask,D,de)
     if inst is None:continue
     cx=np.floor(inst['x']/CELL).astype(int);cy=np.floor(inst['y']/CELL).astype(int)
     for cell in CELLS:
      sel=np.flatnonzero((cx==cell[0])&(cy==cell[1]));n=len(sel)
      if not n:continue
      layercounts[li]+=n
      for j in sel:
       if len(instances)<100:instances.append(dict(tile=[tx,ty],layer=li,definition=di,position=[float(inst[k][j]) for k in ['x','y','z']],scale=[float(inst['sx'][j]),float(inst['sx'][j]),float(inst['sz'][j])],yaw=float(inst['yaw'][j]),spacing=inst['spacing'],acceptance=inst['acceptance'],density=float(inst['density'][j])))
      co=F32(np.cos(inst['yaw'][sel]));si=F32(np.sin(inst['yaw'][sel]));sx=inst['sx'][sel];sz=inst['sz'][sel]
      for g in de['geoms']:
       assert g['material']==344843
       p=g['v']['p'];nv=len(p);rec=np.zeros((n,nv),VTX)
       px=p[None,:,0]*sx[:,None];py=p[None,:,1]*sx[:,None]
       rec['p'][:,:,0]=px*co[:,None]-py*si[:,None]+inst['x'][sel,None]
       rec['p'][:,:,1]=px*si[:,None]+py*co[:,None]+inst['y'][sel,None]
       rec['p'][:,:,2]=p[None,:,2]*sz[:,None]+inst['z'][sel,None]
       nor=g['nor'];nx=np.broadcast_to(nor[None,:,0],(n,nv));ny=np.broadcast_to(nor[None,:,1],(n,nv));nz=np.broadcast_to(nor[None,:,2],(n,nv))
       nn=np.stack([nx*co[:,None]-ny*si[:,None],nx*si[:,None]+ny*co[:,None],np.broadcast_to(nz,(n,nv))],-1)
       # Native 00d26b80 extracts quaternion only and transforms authored normals
       # without scale. Native normal blend1 selects terrain normal; blend0
       # selects quaternion-rotated authored card normals.
       rec['n']=nn*(1.-inst['normal_blend'])+inst['terrain_normal'][sel,None,:]*inst['normal_blend']
       gray=np.trunc(inst['shade'][sel].astype('f8')*inst['brightness'][sel].astype('f8')).astype(np.uint32)
       native_color=np.stack([gray,gray,gray,np.full(n,255,dtype=np.uint32)],-1)
       authored=np.frombuffer(g['v']['color'].astype('<u4').tobytes(),'u1').reshape(nv,4).astype(np.uint32)
       rec['color']=((native_color[:,None,:]*authored[None,:,:])//255).astype('u1')
       # 00d26f1c..00d2702a: normal-rotation-only local z, sink offset,
       # square*curve clamp to0..1, round amplitude0..7; phase8bins.
       local_height=np.maximum(F32(p[None,:,2]-inst['sink'][sel,None]),0.)
       weight=F32(np.clip(F32(local_height.astype('f8')**2*inst['windcurve']),0.,1.))
       amplitude=np.floor(F32(F32(weight.astype('f8')*7.)+.5)).astype(np.uint32)
       phase=(inst['windphase'][sel].astype('f8')*7.999000072479248).astype(np.uint32)
       rec['wind']=((phase[:,None]*8+amplitude)&255)|(inst['windindex'][sel,None]<<8)
       rec['t']=g['v']['uv'][None,:,:]
       vbase=sum(len(x) for x in vertices[cell]);vertices[cell].append(rec.reshape(-1));indices[cell].append((g['idx'][None,:]+np.arange(n)[:,None]*nv+vbase).astype('<u4').ravel())
 report_cells=[]
 index=bytearray((BASE/'index.bin').read_bytes());assert index[:4]==b'OAWI';count=read_u(index,8);updated=0
 for cell in CELLS:
  v=np.concatenate(vertices[cell]) if vertices[cell] else np.zeros(0,VTX);ind=np.concatenate(indices[cell]) if indices[cell] else np.zeros(0,'<u4');payload=struct.pack('<4s3I3I',b'OAWF',len(v),len(ind),1,material_index,0,len(ind))+v.tobytes()+ind.tobytes();name='g%d_%d.bin'%cell;(overlay/name).write_bytes(payload)
  for row in range(count):
   off=20+row*48
   if struct.unpack_from('<2i',index,off)==cell:struct.pack_into('<I',index,off+44,len(ind)//3);updated+=1;break
  old=BASE/name;olddata=old.read_bytes() if old.exists() else None
  report_cells.append(dict(cell=cell,filename=name,vertices=len(v),triangles=len(ind)//3,sha256=sha(payload),old_triangles=read_u(olddata,8)//3 if olddata else None,old_sha256=sha(olddata) if olddata else None,uv_min=v['t'].min(0).tolist() if len(v) else None,uv_max=v['t'].max(0).tolist() if len(v) else None))
 assert updated==len(CELLS),(updated,len(CELLS));(overlay/'index.bin').write_bytes(index)
 def clean(g):return {k:v for k,v in g.items() if k not in ['v','idx','nor']}
 defreport=[dict(layer=li,definitions=[dict(seed=de['seed'],params=de['params'].tolist(),bounds=de['bounds'],offset=de['offset'],end=de['end'],geometry=[dict(**clean(g),vertices=len(g['v']),indices=len(g['idx'])) for g in de['geoms']]) for de in ds]) for li,ds in enumerate(defs)]
 report=dict(vertex_format='OAWF40: pos3float@0, packedWindU32@12, UV2float@16, normal3float@24, RGBA8@36',native_sources=['00d46dd0','00d45f10','00d3ccb0','00d3a810','00d0e2e0','00cec950','00b3aad0','00b0ab40','00d3a350','00d398f0','00d39c80','00d39fd0','00d393e0','00d2ac40'],source_terrain_sha256=sha(terrain),source_stream_sha256=sha(stream),metadata=metadata,native_material=344843,output_material=material_index,seed_examples=seed_examples,definitions=defreport,tiles=tiles,cells=report_cells,instances_by_layer=dict(layercounts),instance_samples=instances,limits=['OAWF stores exact native packed wind bytes. Renderer must index palette using wind&255; second byte wind>>8 is dissolve-related and must not enter64-entry palette.','Float32 Python port reviewed against native assembly, not yet original-kernel bitmatch.','OAWF40 preserves native RGBA8 vertex*instance color and float3 normals; shader must multiply diffuse by vertex RGB. Wind palette producer contract is separate.','Source geometry, exact UVs and native tile ownership are decoded; no random density reduction or atlas substitutions.','Index overlay is based on existing active index; root must merge only selected grass triangle counts with other overlays.'])
 (OUT/'native-foliage-overlay-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(cells=len(report_cells),instances_by_layer=dict(layercounts),triangles=sum(c['triangles'] for c in report_cells),material=material_index,tiles=len(tiles))))
if __name__=='__main__':main()
