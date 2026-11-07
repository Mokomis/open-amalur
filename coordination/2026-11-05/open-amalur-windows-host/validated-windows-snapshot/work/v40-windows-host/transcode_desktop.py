"""Decode original ASTC mip levels once into the isolated Windows asset copy."""
from pathlib import Path
import struct,subprocess,tempfile,time,json,concurrent.futures
from PIL import Image
w=Path(__file__).resolve().parent;tool=w.parents[1]/'tools/astc/bin/astcenc-avx2.exe'
blocks=[(4,4),(5,4),(5,5),(6,5),(6,6),(8,5),(8,6),(8,8),(10,5),(10,6),(10,8),(10,10),(12,10),(12,12)]
scratch=w/'transcode-scratch';scratch.mkdir(exist_ok=True)
files=list((w/'assets/world').glob('t*.bin'));start=time.monotonic()
def convert(p):
 b=p.read_bytes();magic,fmt,width,height,levels=struct.unpack_from('<4s4I',b)
 if magic!=b'OATX' or fmt in [0x8058,0x8c43]:return {'name':p.name,'already_decoded':True}
 srgb=0x93d0<=fmt<=0x93dd;base=0x93d0 if srgb else 0x93b0
 assert 0<=fmt-base<len(blocks),hex(fmt)
 bx,by=blocks[fmt-base];out=bytearray(struct.pack('<4s4I',magic,0x8c43 if srgb else 0x8058,width,height,levels));at=20
 with tempfile.TemporaryDirectory(dir=scratch) as d:
  d=Path(d)
  for level in range(levels):
   n=struct.unpack_from('<I',b,at)[0];at+=4;data=b[at:at+n];at+=n;ww=max(1,width>>level);hh=max(1,height>>level)
   assert n==((ww+bx-1)//bx)*((hh+by-1)//by)*16
   a=d/'mip.astc';t=d/'mip.png';a.write_bytes(struct.pack('<I3B',0x5ca1ab13,bx,by,1)+ww.to_bytes(3,'little')+hh.to_bytes(3,'little')+b'\x01\0\0'+data)
   r=subprocess.run([str(tool),'-dl',str(a),str(t),'-j','1','-silent'],capture_output=True)
   if r.returncode:raise RuntimeError(r.stdout.decode(errors='replace')+r.stderr.decode(errors='replace'))
   with Image.open(t) as image:rgba=image.convert('RGBA').tobytes()
   assert len(rgba)==ww*hh*4;out+=struct.pack('<I',len(rgba))+rgba
 assert at==len(b)
 tmp=p.with_suffix('.desktop-tmp');tmp.write_bytes(out);tmp.replace(p)
 return {'name':p.name,'original_format':hex(fmt),'width':width,'height':height,'levels':levels,'rgba_bytes':len(out)}
results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 for item in pool.map(convert,files):
  results.append(item)
  if len(results)%100==0:print('Decoded',len(results),'/',len(files),flush=True)
(w/'desktop-textures.json').write_text(json.dumps({'seconds':time.monotonic()-start,'decoder':str(tool),'files':results},indent=2))
print('TRANSCODE DONE',len(results),'seconds',round(time.monotonic()-start,2),flush=True)
