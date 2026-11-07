"""Native foliage texture assets with proven packed-channel contracts.
Capture pipeline13098 PS327 uses344837.G as coverage; pipeline13171 PS894
uses344837.R as specular level,344837.B as specular power,3520.R*A/G normalXY.
No active-pack mutation or numerical texture IDs.
"""
from pathlib import Path
import json,struct,io,hashlib
from PIL import Image
root=Path.home()/'Documents/Opem Amalur';src=root/'work/v20-inputs/initial_0.pak';out=root/'work/v44-native-fidelity/foliage-research';receipt=[]
def load(tid):
 q=src/f'{tid}_1.dds';b=q.read_bytes();assert b[16:20]==b'KEEN';w,h=struct.unpack_from('<2H',b,20);fmt=b[29];nm=struct.unpack_from('<H',b,35)[0];o=38;images=[];dims=(w,h)
 for i in range(nm):
  size=((w+3)//4)*((h+3)//4)*(8 if fmt==1 else 16);bc=b[o:o+size];assert len(bc)==size;o+=size
  header=[124,0x81007,h,w,size,0,1]+[0]*11+[32,4,int.from_bytes(b'DXT1' if fmt==1 else b'DXT5','little'),0,0,0,0,0]+[0x1000,0,0,0,0]
  images.append(Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*header)+bc)).convert('RGBA'));w=max(w//2,1);h=max(h//2,1)
 receipt.append(dict(asset=tid,path=str(q),sha256=hashlib.sha256(b).hexdigest(),mips=nm,dimensions=dims,bytes=len(b),parsed_end=o));assert o==len(b);return images
D=load(343428);A=load(344837);N=load(3520);assert len(D)==len(A) and all(d.size==a.size for d,a in zip(D,A))
for d,a in zip(D,A):d.putalpha(a.getchannel('G'))
outputs=[]
for name,im in [('native-grass-diffuse-alpha-343428-344837.oatx',D),('native-grass-alpha-specular-344837.oatx',A),('native-grass-normal-3520.oatx',N)]:
 levels=[i.tobytes() for i in im];b=struct.pack('<4s4I',b'OATX',0x8058,*im[0].size,len(im))+b''.join(struct.pack('<I',len(v))+v for v in levels);(out/name).write_bytes(b);outputs.append(dict(filename=name,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b),dimensions=im[0].size,mips=len(im)))
r=dict(sources=receipt,outputs=outputs,format='OATX RGBA8 native9mipchain retained; originalBC1/BC3decodedwithPillow',alpha_contract='Merged native344837GREEN into diffusealpha; diffuseRGB unchanged. R=speclevel B=specpower in standalone344837RGBA;3520normalRGBA unchanged.',native_material=344843,native_shader=8861,numerical_texture_ids_assigned=False,source_capture_hash_match='Native image15001topBC1 equals343428;15006topBC1 equals344837;15020topBC3 equals3520')
(out/'native-grass-texture-receipt.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
