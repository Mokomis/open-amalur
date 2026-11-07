"""Read-only exact installed source cube -> reviewed OACUBE1 portable carrier."""
from pathlib import Path
import sys,struct,json,hashlib,io
from PIL import Image
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
D=Path(__file__).resolve().parent
src=D/'source/initial_0.pak/1576506.dds'
def sha(b):return hashlib.sha256(b).hexdigest()
b=src.read_bytes()
assert sha(b)=='0460c72ee34d20cbc24827da20db88818be7479983d8c98b4863608be71ba280'
assert b[16:20]==b'KEEN'
w,h=struct.unpack_from('<HH',b,20);fmt=b[29];nl=struct.unpack_from('<H',b,35)[0]
assert (w,h,fmt,nl)==(128,128,1,6)
sizes=[((max(1,w>>k)+3)//4)*((max(1,h>>k)+3)//4)*8 for k in range(nl)]
facebytes=sum(sizes)
assert len(b)==38+6*facebytes
out=b'OACUBE1\0'+struct.pack('<4I',w,h,nl,0x8058)
levels=[]
for k in range(nl):
 ww,hh=max(1,w>>k),max(1,h>>k);parts=[];faces=[]
 for f in range(6):
  off=38+f*facebytes+sum(sizes[:k]);raw=b[off:off+sizes[k]]
  hdr=[124,0x81007,hh,ww,len(raw),0,1]+[0]*11+[32,4,int.from_bytes(b'DXT1','little'),0,0,0,0,0]+[0x1000,0,0,0,0]
  rgba=Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*hdr)+raw)).convert('RGBA').tobytes()
  assert len(rgba)==ww*hh*4
  parts.append(rgba);faces.append({'face':f,'source_offset':off,'source_bc_sha256':sha(raw),'rgba_sha256':sha(rgba)})
  if k==0:Image.frombytes('RGBA',(ww,hh),rgba).save(D/f'face-{f}.png')
 data=b''.join(parts);out+=struct.pack('<I',len(data))+data
 levels.append({'width':ww,'height':hh,'source_mip':k,'bytes':len(data),'sha256':sha(data),'faces':faces})
target=D/'1576506.oacube';target.write_bytes(out)
# independent carrier extent/byte-level round-trip check
q=target.read_bytes();assert q[:8]==b'OACUBE1\0' and struct.unpack_from('<4I',q,8)==(128,128,6,0x8058)
at=24
for k,l in enumerate(levels):
 z=struct.unpack_from('<I',q,at)[0];at+=4;data=q[at:at+z];at+=z
 assert z==6*max(1,128>>k)**2*4 and sha(data)==l['sha256']
assert at==len(q)
manifest={'asset':1576506,'source_file':str(src.relative_to(ROOT)),'source_sha256':sha(b),'source_bytes':len(b),'source_format':'KEEN1 BC1 linear UNORM','source_dimensions':[w,h],'faces':['+X','-X','+Y','-Y','+Z','-Z'],'source_layout':'face-major all mips per face; same reviewed KEEN cube layout as exact source744821-to-native3423 match. No direct original1576506 captured resource join.','runtime_file':str(target.relative_to(ROOT)),'runtime_bytes':len(out),'runtime_sha256':sha(out),'runtime_format':'OACUBE1 RGBA8 (GL_RGBA8=0x8058), mip-major then6tightfaces, unchanged row/channel order','decoded_by':'Pillow standard BC1->RGBA8, reviewed existing exporter; native GPU BC interpolation rounding not bit-claimed','levels':levels,'preserves':'all6authored mips128,64,32,16,8,4; no resize, gamma, generatedmips, faceflip, rotation or R/B swap'}
(D/'cube-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({k:manifest[k] for k in ['runtime_file','runtime_bytes','runtime_sha256','source_dimensions','runtime_format']},indent=2))
