"""Decode source-authored lamp texture levels into private staged OATX assets."""
from pathlib import Path
import sys,json,struct,hashlib
sys.dont_write_bytecode=True
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');O=Path(__file__).resolve().parent;ST=O/'stage';ST.mkdir(exist_ok=True);sys.path.insert(0,str(P/'work/v09-textures'));import keen_texture
C=json.loads((O/'lamp-texture-carriers.json').read_text());N=json.loads((O/'capture/lamp-image-extraction.json').read_text());out=[]
for asset,image,slot,role,existing in [(489069,7829,693,'diffuse',32),(490046,7824,694,'normal',33),(492241,7816,695,'specular',34),(489969,7796,696,'emissive-mask',None)]:
 candidates=[]
 for name in C[str(asset)]:
  q=Path(name);b=q.read_bytes();assert b[16:20]==b'KEEN';tid,ow,oh=struct.unpack_from('<IHH',b);assert tid==asset;shift=struct.unpack_from('<I',b,8)[0];w,h=struct.unpack_from('<HH',b,20);fmt=b[29];n=struct.unpack_from('<H',b,35)[0];at=38;levels=[]
  for k in range(n):
   size=((w+3)//4)*((h+3)//4)*(8 if fmt==1 else 16);levels.append({'width':w,'height':h,'data':b[at:at+size]});at+=size;w=max(1,w//2);h=max(1,h//2)
  assert at==len(b)
  for k,a in enumerate(levels):
   if a['width']==256 and a['height']==256:candidates.append((q,b,fmt,levels[k:],ow,oh,shift))
 assert candidates
 q,b,fmt,levels,ow,oh,shift=min(candidates,key=lambda a:len(a[1]));native=N[str(image)];payload=(O/'capture'/f'native-image-{image}-allmips.bin').read_bytes();offset=0;rgba=[];proof=[]
 assert len(levels)==len(native['level_sizes'])==7
 for k,(a,footprint) in enumerate(zip(levels,native['level_sizes'])):
  block=a['data'];captured=payload[offset:offset+len(block)];offset+=footprint;assert block==captured,(asset,k,'source/captured block mismatch');pixels=keen_texture.decode_blocks(block,a['width'],a['height'],fmt);rgba.append(pixels);proof.append({'level':k,'width':a['width'],'height':a['height'],'compressed_byte_equal_capture':True,'compressed_sha256':hashlib.sha256(block).hexdigest()})
 data=b'OATX'+struct.pack('<4I',0x8058,256,256,len(rgba))+b''.join(struct.pack('<I',len(a))+a for a in rgba);(ST/f't{slot}.bin').write_bytes(data);old={}
 if existing is not None:
  oldb=(P/f'work/v40-windows-host/assets/world/t{existing}.bin').read_bytes();oldn=struct.unpack_from('<I',oldb,20)[0];old={'old_slot':existing,'dimensions':list(struct.unpack_from('<II',oldb,8)),'levels':struct.unpack_from('<I',oldb,16)[0],'whole_oatx_equal':oldb==data,'mip0_equal':oldb[24:24+oldn]==rgba[0]}
 out.append({'asset':asset,'native_image':image,'reserved_texture':slot,'role':role,'file':f't{slot}.bin','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'source':str(q),'source_sha256':hashlib.sha256(b).hexdigest(),'original_dimensions':[ow,oh],'source_shift':shift,'overlapping_source_carriers':len(candidates),'loaded_dimensions':[256,256],'levels':proof,'all_source_blocks_match_native':True,'format':'RGBA8 linear decoded original BC source; seven authored levels; no generated mips','existing_comparison':old})
(O/'lamp-texture-stage.json').write_text(json.dumps(out,indent=2));print(json.dumps([{'asset':r['asset'],'file':r['file'],'bytes':r['bytes'],'source':r['source'],'all7mips_exact':r['all_source_blocks_match_native'],'existing':r['existing_comparison']} for r in out],indent=2))
