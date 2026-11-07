"""Decode three authored BC1 mip chains. No resizing, mip generation, or live writes."""
from pathlib import Path
from PIL import Image
import struct,io,json,hashlib
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent
O=Q/'staged-assets';O.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def rgb565(v):
 r=(v>>11)&31;g=(v>>5)&63;b=v&31
 return ((r<<3)|(r>>2),(g<<2)|(g>>4),(b<<3)|(b>>2),255)
def sample_bc1(blocks,w,x,y):
 at=((y//4)*((w+3)//4)+x//4)*8;c0,c1,bits=struct.unpack_from('<HHI',blocks,at)
 a=rgb565(c0);b=rgb565(c1)
 if c0>c1:
  colors=[a,b,tuple((2*a[k]+b[k])//3 for k in range(3))+(255,),tuple((a[k]+2*b[k])//3 for k in range(3))+(255,)]
 else:colors=[a,b,tuple((a[k]+b[k])//2 for k in range(3))+(255,),(0,0,0,0)]
 return colors[(bits>>(((y%4)*4+x%4)*2))&3]
receipt=[]
for asset,tid,material,old in [(343437,681,293,0),(457709,682,294,17),(566740,683,295,22)]:
 source=P/'work/v20-inputs/DATA_0.pak'/f'{asset}_1.dds';b=source.read_bytes()
 assert b[16:20]==b'KEEN' and b[29]==1
 width,height=struct.unpack_from('<2H',b,20);nm=struct.unpack_from('<H',b,35)[0]
 assert (width,height,nm)==(2048,2048,9)
 off=38;w=width;h=height;levels=[];entries=[]
 for level in range(nm):
  size=((w+3)//4)*((h+3)//4)*8;blocks=b[off:off+size];assert len(blocks)==size;off+=size
  hdr=[124,0x81007,h,w,size,0,1]+[0]*11+[32,4,int.from_bytes(b'DXT1','little'),0,0,0,0,0]+[0x1000,0,0,0,0]
  im=Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*hdr)+blocks)).convert('RGBA');rgba=im.tobytes();assert len(rgba)==w*h*4
  points={(0,0),(w-1,h-1),(w//2,h//2),(w-1,0),(0,h-1)}
  for n in range(128):points.add(((n*173+asset+level*7)%w,(n*359+asset//7+level*13)%h))
  checks=[]
  for x,y in sorted(points):
   decoded=tuple(rgba[(y*w+x)*4:(y*w+x)*4+4]);reference=sample_bc1(blocks,w,x,y)
   assert decoded==reference,(asset,level,x,y,decoded,reference)
   checks.append(dict(x=x,y=y,rgba=decoded))
  levels.append(rgba);entries.append(dict(level=level,width=w,height=h,source_offset=off-size,bc1_bytes=size,bc1_sha256=sha(blocks),rgba_bytes=len(rgba),rgba_sha256=sha(rgba),independent_bc1_samples=len(checks),sample_checks=checks))
  w=max(1,w//2);h=max(1,h//2)
 assert off==len(b) and (entries[-1]['width'],entries[-1]['height'])==(8,8)
 blob=struct.pack('<4s4I',b'OATX',0x8058,width,height,nm)+b''.join(struct.pack('<I',len(rgba))+rgba for rgba in levels)
 # Reparse serialized levels and prove complete decoded payload identity.
 offset=20
 for rgba in levels:
  n=struct.unpack_from('<I',blob,offset)[0];offset+=4;assert blob[offset:offset+n]==rgba;offset+=n
 assert offset==len(blob)
 file=f't{tid}.bin';(O/file).write_bytes(blob)
 receipt.append(dict(asset=asset,new_texture=tid,old_texture=old,material=material,source=str(source.relative_to(P)),source_sha256=sha(b),source_bytes=len(b),width=width,height=height,mips=nm,last_mip=[8,8],format='OATX GL_RGBA8 UNORM; original source BC1 RGBA alpha retained',file='staged-assets/'+file,output_bytes=len(blob),output_sha256=sha(blob),levels=entries))
plan=dict(status='staged only; no active pack mutation',assignments=receipt,texture_count_after_merge=684,materials_patches=[dict(material=r['material'],old_diffuse=r['old_texture'],new_diffuse=r['new_texture'],materials_bin_slot=0,native_materials_bin_texture_slot=0,alpha_texture={293:679,294:680,295:680}[r['material']]) for r in receipt],preserve_global_textures=[0,17,22],reason_append='Existing global textures are shared by legacy cutout rows and retain baked alpha expectations. Append only to family6 rows293..295, which use independent t2.GREEN coverage.',transformations=['BC1decode toRGBA8 only','All9 authored levels2048through8 preserved','No resize, RGB alpha merge, premultiplication, gamma conversion, or generated mipmaps'],validation='Independent BC1 scalar decoder sampled every authored level; serialized fullRGBAlevelbytes reparsed and comparedexact; per-source/per-level/output SHA256 retained',limits=['Stage assets alone; root owns ID reservation, merge, rendering and visual verification','343437 capturedGPU image13901 proven2048x2048 with9mips; other authoredchains verified by sourceheader; captureidentity tracked separately'])
(Q/'authored-leaf-diffuse-manifest.json').write_text(json.dumps(plan,indent=2))
print(json.dumps([dict(asset=r['asset'],texture=r['new_texture'],material=r['material'],bytes=r['output_bytes'],sha256=r['output_sha256'],sample_checks=sum(x['independent_bc1_samples'] for x in r['levels'])) for r in receipt],indent=2))
