"""Source-only ID texture bank. No live asset writes or generated mipmaps."""
from pathlib import Path
import sys,struct,json,hashlib,importlib.util,io
from PIL import Image
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;R=D.parents[2];OUT=D/'textures';OUT.mkdir(exist_ok=True)
sp=importlib.util.spec_from_file_location('assets',R/'work/v49-character-create/analysis/stage_assets.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a);a.STAGE=D
rows=json.loads((D/'all-source-materials.json').read_text());ids={t['id'] for m in rows for t in m['textures'] if t['id']>1}
pal=json.loads((R/'work/v49-character-create/analysis/resolved-cosmetic-palettes.json').read_text())
for cats in pal['types'].values():
 for rec in cats['SkinTone']['records']:ids.update(x for x in rec['words'][3:5] if x>1)
app=json.loads((R/'work/v50-character-complete/appearance-assets/appearance-source-catalogue.json').read_text())
# Type tattoo data are resolved by appearance producer. Additional IDs accepted explicitly.
extra=D/'extra-textures.json'
if extra.exists():ids.update(json.loads(extra.read_text()))
names=sorted({n for ns in a.LIST.values() for n in ns if n.endswith('.dds') and n.split('.')[0].split('_')[0].strip().isdigit() and int(n.split('.')[0].split('_')[0].strip()) in ids})
fs=a.extract(names);(D/'texture-extraction.json').write_text(json.dumps({k:str(p.relative_to(R)) for k,p in fs.items()},indent=2),encoding='utf-8')
def sha(b):return hashlib.sha256(b).hexdigest()
textures=[];errors=[];cubes=[]
for tid in sorted(ids):
 choices=[]
 for name,p in fs.items():
  if int(name.split('.')[0].split('_')[0])!=tid:continue
  b=p.read_bytes()
  if b[16:20]!=b'KEEN':continue
  w,h=struct.unpack_from('<HH',b,20);fmt=b[29];nl=struct.unpack_from('<H',b,35)[0]
  if fmt not in [1,2,5]:errors.append(dict(asset=tid,file=name,error='unreviewedformat',format=fmt));continue
  size=sum(((max(1,w>>k)+3)//4)*((max(1,h>>k)+3)//4)*(8 if fmt in [1,2] else 16) for k in range(nl))
  if len(b)==38+size*6:cubes.append(dict(asset=tid,source=str(p.relative_to(R)),width=w,height=h,mips=nl,format=fmt,sha256=sha(b)));continue
  if len(b)!=38+size:errors.append(dict(asset=tid,file=name,error='carrier size',bytes=len(b),expected=38+size));continue
  choices.append((w*h,nl,p,b,w,h,fmt))
 if not choices:
  if not any(x['asset']==tid for x in cubes):errors.append(dict(asset=tid,error='no complete2D chain'))
  continue
 _,nl,p,b,w,h,fmt=max(choices,key=lambda q:(q[0],q[1]));at=38;chunks=[];levels=[];start=None
 for k in range(nl):
  ww,hh=max(1,w>>k),max(1,h>>k);z=((ww+3)//4)*((hh+3)//4)*(8 if fmt in [1,2] else 16);raw=b[at:at+z];at+=z
  if max(ww,hh)>512:continue
  if start is None:start=k
  head=[124,0x81007,hh,ww,len(raw),0,1]+[0]*11+[32,4,int.from_bytes(b'DXT1' if fmt in [1,2] else b'DXT5','little'),0,0,0,0,0]+[0x1000,0,0,0,0]
  pixels=Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*head)+raw)).convert('RGBA').tobytes()
  chunks.append(pixels);levels.append(dict(source_mip=k,width=ww,height=hh,source_bc_sha256=sha(raw),rgba_sha256=sha(pixels)))
 if start is None:errors.append(dict(asset=tid,error='no portable authored mip'));continue
 out=b'OATX'+struct.pack('<4I',0x8c43 if fmt==2 else 0x8058,max(1,w>>start),max(1,h>>start),len(chunks))+b''.join(struct.pack('<I',len(x))+x for x in chunks)
 target=OUT/f'{tid}.oatx'
 if target.exists():assert target.read_bytes()==out
 else:target.write_bytes(out)
 textures.append(dict(asset=tid,source=str(p.relative_to(R)),source_sha256=sha(b),source_width=w,source_height=h,source_format=fmt,first_source_mip=start,file=str(target.relative_to(D)),bytes=len(out),sha256=sha(out),levels=levels))
 if len(textures)%40==0:print('staged',len(textures),flush=True)
report=dict(textures=textures,cubes=cubes,errors=errors,policy='NativeUNORM RGB/RGBA; <=512 highestcomplete authoredtail; preserve row/channel order, all authored lowerlevels; no resize/gamma/generatedmip',portable_bytes=sum(x['bytes'] for x in textures))
(D/'texture-bank-manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('DONE',len(textures),'cubes',len(cubes),'errors',len(errors),'bytes',report['portable_bytes'],flush=True)
