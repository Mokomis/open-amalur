from pathlib import Path
import sys,json,struct,hashlib,shutil,ast,io
from PIL import Image
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[2];Q=R/'work/v48-opening/content-audit'
sys.path.insert(0,str(Q));import content_sources as C
C.OUT=O/'new-texture-inputs';C.OUT.mkdir(exist_ok=True)
H=R/'work/v44-native-fidelity/foliage-research/leaf-authored-auxiliary/build_authored_leaf_auxiliary.py'
tree=ast.parse(H.read_text());defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['rgb565','ref_sample']]
exec(compile(ast.Module(body=defs,type_ignores=[]),str(H),'exec'))
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 mats=json.loads((O/'material-contracts.json').read_text())
 assets=sorted({x['asset'] for m in mats for x in m['texture_slots']})
 oldroot=Q/'candidate-first-room';old=json.loads((oldroot/'texture-stage-manifest.json').read_text())
 oldtex={t['asset']:t for t in old['textures']};oldcube={t['asset']:t for t in old['cubemaps']}
 need=[a for a in assets if a not in oldtex and a not in oldcube]
 names=[n for a in need for n in [f'{a}.dds']+[f'{a}_{k}.dds' for k in range(6)]]
 fs=C.extract(names);records=[];cubes=[]
 for sub in ['textures-native-bc','textures-portable-512','textures-cube-native']:(O/sub).mkdir(exist_ok=True)
 for a in assets:
  if a in oldcube:
   rec=oldcube[a];b=(oldroot/rec['file']).read_bytes();assert sha(b)==rec['source_sha256']
   (O/rec['file']).write_bytes(b);cubes.append({**rec,'reused_manifest':str((oldroot/'texture-stage-manifest.json').relative_to(R))});continue
  if a in oldtex:
   rec=oldtex[a]
   for k,h in [('native_bc_file','native_bc_sha256'),('portable_file','portable_sha256')]:
    b=(oldroot/rec[k]).read_bytes();assert sha(b)==rec[h];(O/rec[k]).write_bytes(b)
   records.append({**rec,'reused_manifest':str((oldroot/'texture-stage-manifest.json').relative_to(R))});continue
  cs=[]
  for n in [f'{a}.dds']+[f'{a}_{k}.dds' for k in range(6)]:
   if n not in fs:continue
   b=fs[n].read_bytes();assert b[16:20]==b'KEEN'
   w,h=struct.unpack_from('<2H',b,20);fmt=b[29];nm=struct.unpack_from('<H',b,35)[0]
   at=38;ww,hh=w,h;lev=[]
   if fmt not in [1,5]:continue
   for i in range(nm):
    size=((ww+3)//4)*((hh+3)//4)*(8 if fmt==1 else 16)
    lev.append(dict(level=i,width=ww,height=hh,source_offset=at,bytes=size));at+=size;ww,hh=max(1,ww//2),max(1,hh//2)
   if at==len(b):cs.append(dict(path=fs[n],raw=b,width=w,height=h,format=fmt,mips=nm,levels=lev))
  assert cs,('No complete supported2D carrier',a)
  c=max(cs,key=lambda x:(x['width']*x['height'],x['mips']))
  chunks=[c['raw'][l['source_offset']:l['source_offset']+l['bytes']] for l in c['levels']]
  bc=struct.pack('<4s4I',b'OATX',0x83f1 if c['format']==1 else 0x83f3,c['width'],c['height'],c['mips'])+b''.join(struct.pack('<I',len(b))+b for b in chunks)
  start=next(i for i,l in enumerate(c['levels']) if max(l['width'],l['height'])<=512)
  out=[];receipts=[]
  for i in range(start,c['mips']):
   l=c['levels'][i];data=chunks[i];w,h=l['width'],l['height']
   header=[124,0x81007,h,w,len(data),0,1]+[0]*11+[32,4,int.from_bytes(b'DXT1' if c['format']==1 else b'DXT5','little'),0,0,0,0,0]+[0x1000,0,0,0,0]
   rgba=Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*header)+data)).convert('RGBA').tobytes()
   pts={(0,0),(w-1,h-1),(w//2,h//2)}|{((j*173+a+i*7)%w,(j*359+a//7+i*13)%h) for j in range(32)}
   for x,y in pts:assert tuple(rgba[(y*w+x)*4:(y*w+x)*4+4])==ref_sample(data,w,x,y,c['format'])
   receipts.append(dict(source_level=i,width=w,height=h,rgba_sha256=sha(rgba),samples=len(pts)));out.append(rgba)
  w,h=c['levels'][start]['width'],c['levels'][start]['height']
  portable=struct.pack('<4s4I',b'OATX',0x8058,w,h,len(out))+b''.join(struct.pack('<I',len(b))+b for b in out)
  name=f'asset-{a}.oatx';(O/'textures-native-bc'/name).write_bytes(bc);(O/'textures-portable-512'/name).write_bytes(portable)
  records.append(dict(asset=a,name=C.SYMS['texture'][str(a)],source=str(c['path'].relative_to(R)),source_sha256=sha(c['raw']),source_width=c['width'],source_height=c['height'],source_mips=c['mips'],source_format=c['format'],native_bc_file='textures-native-bc/'+name,native_bc_sha256=sha(bc),native_bc_bytes=len(bc),native_bc_levels=[{**l,'bc_sha256':sha(chunks[i])} for i,l in enumerate(c['levels'])],portable_file='textures-portable-512/'+name,portable_sha256=sha(portable),portable_bytes=len(portable),portable_source_first_mip=start,portable_width=w,portable_height=h,portable_levels=receipts))
 for rec in records:
  for k,h in [('native_bc_file','native_bc_sha256'),('portable_file','portable_sha256')]:
   b=(O/rec[k]).read_bytes();assert sha(b)==rec[h];magic,fmt,w,h,n=struct.unpack_from('<4s4I',b);assert magic==b'OATX';at=20
   for i in range(n):size=struct.unpack_from('<I',b,at)[0];at+=4+size
   assert at==len(b)
 report=dict(textures=records,cubemaps=cubes,policy='Exact source UNORM BC payloads plus explicit <=512 authored mip-tail RGBA profile; no generated mips/resizing; not original runtime residency evidence.',count_2d=len(records),count_cubes=len(cubes),native_bc_bytes=sum(r['native_bc_bytes'] for r in records),portable_bytes=sum(r['portable_bytes'] for r in records),new_texture_assets=need)
 (O/'texture-stage-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ['count_2d','count_cubes','native_bc_bytes','portable_bytes','new_texture_assets']}))
if __name__=='__main__':main()
