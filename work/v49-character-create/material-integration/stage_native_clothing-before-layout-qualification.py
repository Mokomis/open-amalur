"""Read only source export: four actual Almain clothing HardLight materials.
Outputs only below native-clothing-stage; never replaces a current pack."""
from pathlib import Path
import sys,struct,json,hashlib,ast,io
from PIL import Image
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;O=D/'native-clothing-stage';O.mkdir(exist_ok=True)
A=P/'work/v49-character-create/vertex-contract-audit'
def sha(b):return hashlib.sha256(b).hexdigest()
tool=P/'work/v44-native-fidelity/foliage-research/leaf-authored-auxiliary/build_authored_leaf_auxiliary.py'
defs=[n for n in ast.parse(tool.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name in ['rgb565','ref_sample']]
assert len(defs)==2
exec(compile(ast.Module(body=defs,type_ignores=[]),str(tool),'exec'))
keys={10276250:'ConstantColor',11960536:'SpecularValues',23195542:'CharacterExtraTerms2',10120212:'FresnelValues2'}
ids=[660426,660428,660429,660430];profiles=[];needed=set()
for mid in ids:
 m=json.loads((A/f'materials/{mid}.json').read_text());assert m['shader_id']==545212
 params={keys[p['key']]:list(struct.unpack('<4f',bytes.fromhex(p['value_bytes']))) for p in m['parameters']};assert set(params)==set(keys.values())
 slots={p['source_slot']:p['texture_id'] for p in m['source_slots']};assert set(slots)=={0,1,2,3} and slots[1]==250070
 needed.update(slots[s] for s in [0,2,3])
 profiles.append(dict(material=mid,shader=545212,source_material=m['path'],source_material_sha256=m['sha256'],parameters=params,texture_source_slots=slots,used_slots=[0,2,3],unused_slot1='Authored white250070 is optimized out by recovered opaqueHardLight PS; no fabricated fallback'))
ex=json.loads((D/'native-texture-inputs/extraction-receipt.json').read_text());fs={n:P/p for n,p in ex['effective_by_archive_precedence'].items()};textures=[]
for tid in sorted(needed):
 carriers=[]
 for name in [f'{tid}.dds']+[f'{tid}_{i}.dds' for i in range(6)]:
  if name not in fs:continue
  f=fs[name];b=f.read_bytes();assert b[16:20]==b'KEEN';w,h=struct.unpack_from('<HH',b,20);fmt=b[29];nl=struct.unpack_from('<H',b,35)[0];assert fmt in [1,5]
  at=38;levels=[];ww,hh=w,h
  for level in range(nl):
   size=((ww+3)//4)*((hh+3)//4)*(8 if fmt==1 else 16);levels.append(dict(level=level,width=ww,height=hh,offset=at,bytes=size));at+=size;ww=max(1,ww//2);hh=max(1,hh//2)
  if at==len(b):carriers.append(dict(path=f,raw=b,width=w,height=h,fmt=fmt,levels=levels))
 assert carriers,tid
 c=max(carriers,key=lambda c:(c['width']*c['height'],len(c['levels']),len(c['raw'])));b=c['raw'];lev=c['levels'];start=next(i for i,l in enumerate(lev) if max(l['width'],l['height'])<=512)
 chunks=[b[l['offset']:l['offset']+l['bytes']] for l in lev]
 bc=b'OATX'+struct.pack('<4I',0x83f1 if c['fmt']==1 else 0x83f3,c['width'],c['height'],len(lev))+b''.join(struct.pack('<I',len(v))+v for v in chunks)
 rgba=[];records=[]
 for i,l in enumerate(lev[start:],start):
  data=chunks[i];w,h=l['width'],l['height'];head=[124,0x81007,h,w,len(data),0,1]+[0]*11+[32,4,int.from_bytes(b'DXT1' if c['fmt']==1 else b'DXT5','little'),0,0,0,0,0]+[0x1000,0,0,0,0]
  pixels=Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*head)+data)).convert('RGBA').tobytes()
  points={(0,0),(w-1,h-1),(w//2,h//2)}|{((j*173+tid+i*7)%w,(j*359+tid//7+i*13)%h) for j in range(32)}
  for x,y in points:assert tuple(pixels[(y*w+x)*4:(y*w+x)*4+4])==ref_sample(data,w,x,y,c['fmt']),(tid,i,x,y)
  rgba.append(pixels);records.append(dict(source_level=i,width=w,height=h,rgba_sha256=sha(pixels),scalar_samples=len(points)))
 portable=b'OATX'+struct.pack('<4I',0x8058,lev[start]['width'],lev[start]['height'],len(rgba))+b''.join(struct.pack('<I',len(v))+v for v in rgba)
 bcfile=O/f'{tid}-source-bc.oatx';rgbaFile=O/f'{tid}-portable512.oatx';assert not bcfile.exists() and not rgbaFile.exists();bcfile.write_bytes(bc);rgbaFile.write_bytes(portable)
 for blob,data in [(bc,chunks),(portable,rgba)]:
  at=20
  for v in data:n=struct.unpack_from('<I',blob,at)[0];at+=4;assert blob[at:at+n]==v;at+=n
  assert at==len(blob)
 textures.append(dict(asset=tid,source=str(c['path'].relative_to(P)),source_sha256=sha(b),width=c['width'],height=c['height'],format=c['fmt'],native_file=bcfile.name,native_sha256=sha(bc),portable_file=rgbaFile.name,portable_sha256=sha(portable),portable_bytes=len(portable),first_source_mip=start,levels=records,all_carriers=[dict(path=str(x['path'].relative_to(P)),sha256=sha(x['raw']),width=x['width'],height=x['height'],mips=len(x['levels'])) for x in carriers]))
m=json.loads((A/'source-join-manifest.json').read_text());parts=[dict(part=p['part'],material=p['material_id'],shader=p['shader_id'],fab=p['fab'],assembly=p['assembly'],vertices=p['vertices'],flags=p['flags'],source_type=p['vertex_type'],stride=p['source_stride']) for p in m['parts'] if p['material_id'] in ids]
assert len(parts)==4 and all(p['stride']==60 and p['source_type']==22 and p['flags']&32 for p in parts)
report=dict(status='STAGED ONLY, no renderer/native skin admission',source_pack_sha256=m['pack_sha256'],source_attribute_sha256=m['sidecar_sha256'],materials=profiles,parts=parts,textures=textures,portable_bytes=sum(t['portable_bytes'] for t in textures),decoder_source=str(tool.relative_to(P)),decoder_sha256=sha(tool.read_bytes()),policy='Preserve highest complete authored BC chain; optional <=512 authored mip-tail, no resizing/generated mipmaps. ExplicitGL_TEXTURE_MAX_LEVEL is required because authored chains stop at4x4.',limits=['Active weightedHardLight vertex permutation/basis output is not established by standalone rigidVS351 proof.','Source material/shader/texture links are exact, runtime instance tint/samplers/permutation are separate.','Current tested scene still uses old diffuse-only character path; this stage does not make full creator appearance work.','All UI must extend existing new oa_ui/oa_menu.'])
(O/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(dict(materials=len(profiles),parts=parts,textures=len(textures),portable_bytes=report['portable_bytes']),indent=2))
