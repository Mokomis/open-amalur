"""Read existing extracted native assets; emit only into a selected new output.
No extraction/install, core edits or game process. Noon bridge contract only."""
from pathlib import Path
import argparse,struct,json,hashlib,sys
a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=Path.home()/'Documents/Opem Amalur');a.add_argument('--output',type=Path,required=True);a.add_argument('--rgba',action='store_true');ns=a.parse_args();out=ns.output;out.mkdir(parents=True,exist_ok=True);inp=ns.root/'work/v20-inputs'
def choose(name):
 for pak in ['patch_0.pak','initial_0.pak','DATA_0.pak']:
  q=inp/pak/name
  if q.exists():return q
 raise FileNotFoundError(name)
f=choose('325844.sky_bxml');b=f.read_bytes();at=0;keys=[]
for key in range(4):
 n=struct.unpack_from('<I',b,at)[0];at+=8;colors=[];stops=[0.]
 for i in range(n):
  c=struct.unpack_from('<I',b,at)[0];at+=4;colors.append(((c>>16)&255,(c>>8)&255,c&255,c>>24))
  if i<n-1:stops.append(struct.unpack_from('<f',b,at)[0]);at+=4
 keys.append((colors,stops))
assert at==272;colors,stops=keys[2];assert all(stops[i+1]>stops[i] for i in range(len(stops)-1))
gradient=bytearray()
for i in range(32):
 t=i/32;j=next((j for j in range(len(stops)-1) if stops[j]<=t<stops[j+1]),len(stops)-2);u=(t-stops[j])/(stops[j+1]-stops[j])
 gradient+=bytes(int(colors[j][k]+(colors[j+1][k]-colors[j][k])*u) for k in range(4))
(out/'noon-gradient32.rgba').write_bytes(gradient)
# These offset semantics are confirmed by byte-matching active Vulkan textures,
# not inferred solely from the older build_sky.py variable names.
lower=struct.unpack_from('<I',b,480+2*4)[0];upper=struct.unpack_from('<I',b,464+2*4)[0]
report=dict(skyfile=str(f),sky_sha256=hashlib.sha256(b).hexdigest(),gradient_noon_sha256=hashlib.sha256(gradient).hexdigest(),lower_id=lower,upper_id=upper,clouds=[])
for role,tid in [('lower',lower),('upper',upper)]:
 f=choose(f'{tid}_1.dds');d=f.read_bytes();w,h=struct.unpack_from('<HH',d,20);fmt=d[29];levels=struct.unpack_from('<H',d,35)[0];assert fmt==5
 at=38;parts=[];meta=[]
 for level in range(levels):
  lw=max(1,w>>level);lh=max(1,h>>level);size=((lw+3)//4)*((lh+3)//4)*16;part=d[at:at+size];assert len(part)==size;parts.append(part);meta.append(dict(level=level,w=lw,h=lh,offset=at-38,bytes=size,sha256=hashlib.sha256(part).hexdigest()));at+=size
 assert at==len(d)
 raw=b''.join(parts);name=f'{role}-{tid}-{w}x{h}.bc3';(out/name).write_bytes(raw)
 c=dict(role=role,id=tid,source=str(f),source_sha256=hashlib.sha256(d).hexdigest(),file=name,format='BC3_UNORM',w=w,h=h,levels=meta)
 if ns.rgba:
  sys.path.insert(0,str(ns.root/'work/v09-textures'));import keen_texture
  oatx=out/f'native-sky-{role}.oatx'
  with oatx.open('wb') as target:
   target.write(b'OATX'+struct.pack('<4I',0x8058,w,h,levels))
   for m,part in zip(meta,parts):
    pix=bytes(keen_texture.decode_blocks(part,m['w'],m['h'],fmt));assert len(pix)==m['w']*m['h']*4
    target.write(struct.pack('<I',len(pix)));target.write(pix);m['rgba_sha256']=hashlib.sha256(pix).hexdigest()
  c['oatx_file']=oatx.name;c['oatx_sha256']=hashlib.sha256(oatx.read_bytes()).hexdigest()
 report['clouds'].append(c)
(out/'sky-assets.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
