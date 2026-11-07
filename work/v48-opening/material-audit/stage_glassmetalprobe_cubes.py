"""Stage authored glassmetalprobe cubes as OAWP2. No live assets are written.
Native source face ordinal and rows are retained. Standard BC1->RGBA8 decode,
without R/B swap, rotation, vertical flip, resizing or generated mip levels."""
from pathlib import Path
import json,struct,hashlib,sys,io
from PIL import Image
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
OUT=ROOT/'work/v48-opening/material-audit'
sys.path.insert(0,str(ROOT/'work/v49-character-create/analysis'))
import stage_assets as assets
assets.STAGE=OUT
def sha(b):return hashlib.sha256(b).hexdigest()
ids=[1259503,505647]
paths=assets.extract([f'{i}.dds' for i in ids])
blob=bytearray(struct.pack('<4s3I',b'OAWP',2,len(ids),0));metadata=[]
for asset in ids:
 path=paths[f'{asset}.dds'];raw=path.read_bytes()
 assert raw[16:20]==b'KEEN' and raw[28]==3 and raw[29]==1
 w0,h0=struct.unpack_from('<2H',raw,20);nm=struct.unpack_from('<H',raw,35)[0]
 assert w0==h0 and w0<=512 and nm<=16
 faces=[];at=38;records=[]
 for face in range(6):
  levels=[]
  for lev in range(nm):
   w,h=max(1,w0>>lev),max(1,h0>>lev);n=((w+3)//4)*((h+3)//4)*8;bc=raw[at:at+n];assert len(bc)==n
   header=[124,0x81007,h,w,n,0,1]+[0]*11+[32,4,int.from_bytes(b'DXT1','little'),0,0,0,0,0]+[0x1000,0,0,0,0]
   rgba=Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*header)+bc)).convert('RGBA').tobytes()
   levels.append(rgba);records.append({'face_ordinal':face,'level':lev,'width':w,'height':h,'source_offset':at,'source_bytes':n,'source_bc_sha256':sha(bc),'rgba_sha256':sha(rgba)})
   at+=n
  faces.append(levels)
 assert at==len(raw),(asset,at,len(raw))
 total=sum(len(v) for face in faces for v in face);blob+=struct.pack('<6I',asset,6,w0,h0,nm,total)
 for lev in range(nm):
  w,h=max(1,w0>>lev),max(1,h0>>lev);level=b''.join(faces[face][lev] for face in range(6))
  blob+=struct.pack('<3I',w,h,len(level))+level
 metadata.append({'asset_id':asset,'source':str(path),'source_sha256':sha(raw),'source_format':'KEENtype3cube,BC1format1,face-major,mips within face','dimensions':[w0,h0],'authored_levels':nm,'retained_levels':nm,'base_source_level':0,'face_ordinal_order':[0,1,2,3,4,5],'GL_upload_targets':['+X','-X','+Y','-Y','+Z','-Z'],'pixel_policy':'Standard BC1 RGB565 decode to RGBA8, unchanged stored face/row order; no R/B swap, flips, rotation, resize or generated mips. BC software/GPU rounding identity not claimed.','records':records})
p=OUT/'glassmetalprobe-probes.bin';p.write_bytes(blob)
# Independently walk the existing loader's container contract.
at=16;validated=[]
for wanted in ids:
 matched=False;off=16
 for _ in ids:
  asset,faces,w0,h0,nm,total=struct.unpack_from('<6I',blob,off);off+=24;nbytes=0
  for lev in range(nm):
   w,h,n=struct.unpack_from('<3I',blob,off);off+=12
   assert (w,h,n)==(max(1,w0>>lev),max(1,h0>>lev),max(1,w0>>lev)*max(1,h0>>lev)*faces*4)
   nbytes+=n;assert off+n<=len(blob);off+=n
  assert nbytes==total
  if asset==wanted:matched=True
 assert off==len(blob) and matched;validated.append(wanted)
receipt={'output':str(p),'sha256':sha(blob),'bytes':len(blob),'format':'OAWPversion2;2textures;0materials;matches oa_cart_probe_open','cubes':metadata,'container_wanted_ids_validated':validated,'source_face_capture_comparison':'Not captured in existing Gorhart reference; retains source ordinal and existing OAWP2/DDS convention. No invented face/channel remap.'}
(OUT/'glassmetalprobe-probes.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({'file':str(p),'sha256':sha(blob),'bytes':len(blob),'cubes':[(x['asset_id'],x['dimensions'],x['authored_levels']) for x in metadata]}))
