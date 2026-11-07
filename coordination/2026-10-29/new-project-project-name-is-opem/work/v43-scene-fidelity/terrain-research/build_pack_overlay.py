"""Produce reviewed overlay files only, never write the active pack."""
from pathlib import Path
import io,json,struct,subprocess,hashlib,collections,math,sys
import numpy as np
from PIL import Image
root=Path.home()/'Documents/Opem Amalur';research=root/'work/v43-scene-fidelity/terrain-research';base=root/'work/v40-windows-host/assets/world';out=research/'pack-overlay';out.mkdir(exist_ok=True);sources=research/'source-textures';sources.mkdir(exist_ok=True)
P=json.loads((research/'palette-evidence.json').read_text());proposal=json.loads((research/'proposal/native-material-grid-reference.json').read_text());M=(base/'materials.bin').read_bytes();mc=struct.unpack_from('<I',M)[0];assert len(M)==4+mc*28;oldrows=[struct.unpack_from('<7I',M,4+i*28) for i in range(mc)];texbase=max(int(q.stem[1:]) for q in base.glob('t*.bin'))+1;ids=sorted({x for r in P['rows'] for x in [r['diffuse'],r['normal']]});id_to_tex={v:texbase+i for i,v in enumerate(ids)};g=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning');textures=[]
for tid in ids:
 name=f'{tid}_1.dds';q=sources/name
 if not q.exists():
  subprocess.run([str(g/'modding/pakfileunpacker.exe'),str(g/'data/DATA_0.pak'),'unpack',str(sources),name],cwd=g/'modding',capture_output=True,timeout=30,check=True)
 b=q.read_bytes();assert b[16:20]==b'KEEN';w,h=struct.unpack_from('<2H',b,20);fmt=b[29];assert w==h and w<=4096 and fmt in [1,5];mip_offset=38
 while w>1024:
  mip_offset+=((w+3)//4)*((h+3)//4)*(8 if fmt==1 else 16);w//=2;h//=2
 size=((w+3)//4)*((h+3)//4)*(8 if fmt==1 else 16);bc=b[mip_offset:mip_offset+size];fourcc=int.from_bytes(b'DXT1' if fmt==1 else b'DXT5','little');header=[124,0x81007,h,w,size,0,1]+[0]*11+[32,4,fourcc,0,0,0,0,0]+[0x1000,0,0,0,0];assert len(header)==31
 im=Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*header)+bc)).convert('RGBA');levels=[];alpha=im.getchannel('A');alpha_range=alpha.getextrema()
 while True:
  levels.append(im.tobytes())
  if im.size==(1,1):break
  im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.BOX)
 tx=id_to_tex[tid];payload=struct.pack('<4s4I',b'OATX',0x8058,w,h,len(levels))+b''.join(struct.pack('<I',len(v))+v for v in levels);(out/f't{tx}.bin').write_bytes(payload);textures.append(dict(asset_id=tid,texture_index=tx,source_file=str(q),source_sha256=hashlib.sha256(b).hexdigest(),width=w,height=h,levels=len(levels),alpha_min=alpha_range[0],alpha_max=alpha_range[1],output_sha256=hashlib.sha256(payload).hexdigest()))
newrows=[];side=bytearray(struct.pack('<4s2I',b'OATP',1,len(P['sets'])));profiles=[]
for S in P['sets']:
 rows=[P['rows'][i] for i in S['row_indices']];tids=[r['diffuse'] for r in rows]+[r['normal'] for r in rows];tex=[id_to_tex[i] for i in tids];scales=[r['uv_scale']*.5 for r in rows];mi=mc+S['index'];newrows.append((0x40000001,*tex[:6]));side+=struct.pack('<2I8I4f',mi,S['index'],*tex,*scales);profiles.append(dict(material=mi,native_set=S['index'],texture_indices=tex,source_texture_ids=tids,map_uv_scales=scales))
(out/'materials.bin').write_bytes(struct.pack('<I',mc+len(newrows))+M[4:]+b''.join(struct.pack('<7I',*r) for r in newrows));(out/'terrain_materials.bin').write_bytes(side)
selector=np.frombuffer((research/'proposal/terrain-431658-selector.r8ui').read_bytes(),np.uint8).reshape(4096,4096);C=collections.Counter();cell_reports=[]
# Only explicitly selected Gorhart reference area, all three LODs. Other cells
# and cells with any unowned source triangles retain their original draws.
reference_cells=sorted({(ix,iy) for ix in [-1,0,1] for iy in [-11,-10,-9]}|{(ix,iy) for ix in [0,1,2] for iy in [-15,-14,-13]})
for ix,iy in reference_cells:
 if True:
  staged=[];reason=None
  for lod in range(3):
   q=base/f'c{ix}_{iy}_{lod}.bin'
   if not q.exists():reason='missing cell';break
   b=q.read_bytes();magic,nv,ni,nd=struct.unpack_from('<4s3I',b);assert magic==b'OAWC';at=16+nd*12;tail=b[at:];assert len(tail)==nv*28+ni*4;V=np.ndarray((nv,3),'<f4',buffer=tail,strides=(28,4));I=np.frombuffer(tail,'<u4',offset=nv*28,count=ni);draw=[];grounds=0
   for j in range(nd):
    mid,first,count=struct.unpack_from('<3I',b,16+j*12);assert first+count<=ni
    if not oldrows[mid][0]&1:draw.append((mid,first,count));continue
    draw.append((mid,first,count)) # Parent shader suppresses legacy only for valid native selector fragments.
    pts=V[I[first:first+count]];lo=pts[:,:2].min(0);hi=pts[:,:2].max(0);mn=np.floor((lo+102425)/50).astype(int);mx=np.floor((hi+102425)/50).astype(int)
    if (mn<0).any() or (mx>=4096).any():continue
    window=selector[mn[1]:mx[1]+1,mn[0]:mx[0]+1];a=window&7;bb=(window>>3)&7
    needed=sorted(set(np.unique(a[a<5]).tolist()+np.unique(bb[bb<5]).tolist()));draw.extend((mc+s,first,count) for s in needed);grounds+=1
   if reason:break
   assert len(draw)<=128,('draw capacity',ix,iy,lod,len(draw));payload=struct.pack('<4s3I',b'OAWC',nv,ni,len(draw))+b''.join(struct.pack('<3I',*r) for r in draw)+tail
   # Strong geometry identity: only draw records differ. Vertex/index bytes exact.
   assert payload[16+len(draw)*12:]==b[16+nd*12:]
   staged.append((q.name,payload,dict(lod=lod,old_draws=nd,new_draws=len(draw),ground_draws=grounds,geometry_sha256=hashlib.sha256(tail).hexdigest())))
  if reason:
   C['cells_skipped']+=1;cell_reports.append(dict(cell=[ix,iy],patched=False,reason=reason));continue
  for name,data,report in staged:(out/name).write_bytes(data)
  C['cells_patched']+=1;cell_reports.append(dict(cell=[ix,iy],patched=True,lods=[v[2] for v in staged]))
index=bytearray((base/'index.bin').read_bytes());struct.pack_into('<I',index,12,texbase+len(ids));(out/'index.bin').write_bytes(index);water=(base/'water.bin').read_bytes();assert len(water)==4+mc*44 and struct.unpack_from('<I',water)[0]==mc;(out/'water.bin').write_bytes(struct.pack('<I',mc+len(newrows))+water[4:]+b'\0'*(len(newrows)*44))
# Global maps have explicit filenames; they do not consume ordinary texture IDs.
with Image.open(research/'proposal/terrain-431658-paint-linear-rgba.png') as im:rgba=im.convert('RGBA').tobytes()
(out/'terrain_paint.bin').write_bytes(struct.pack('<4s4I',b'OATX',0x8058,4097,4097,1)+struct.pack('<I',len(rgba))+rgba);(out/'terrain_selector.bin').write_bytes(selector.tobytes())
report=dict(base=str(base),output=str(out),counts=C,base_material_count=mc,new_material_count=mc+len(newrows),texture_base=texbase,new_texture_count=texbase+len(ids),profiles=profiles,textures=textures,cells=cell_reports,legacy_terrain_draws_retained=True,feature_gate=32,fallback_contract='Legacy terrain draws discard only when feature32 enabled and fragment selector chosen materialSet<5. Native draws discard when feature32 disabled or selector chosen materialSet!=draw expected set. Out-of-domain,ID7 and255 stay legacy.',geometry_vertex_index_bytes_unchanged=True,index_cell_count_bounds_triangle_metadata_unchanged=True,terrain_material_flag='0x40000000 marks native terrain; bit0 remains terrain',sidecar_format='OATP,u32version1,u32count; perrow <2I8I4f>: materialIndex,nativeSetID,diffuseTex[4],normalTex[4],mapUVScale[4]',diffuse_alpha_preserved=True,mip_policy='At most1024 source mip (_1 with original higher levels skipped); decoded BC1/BC3 with existing Pillow; full generated box mips down to1x1; no alpha replacement. GPU BC rounding and normal-map mip renormalization parity are unverified.',deployment=False)
(research/'pack-overlay-report.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k not in ['textures','cells']},indent=2));print('CELLS',cell_reports)
