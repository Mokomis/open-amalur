"""Extract only the three active ambient InitImage payloads, no replay/GPU."""
from pathlib import Path
import struct,json,hashlib
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
OUT=ROOT/'work/v49-character-create/character-ambient-audit'
CAP=ROOT/'work/v31-native-slice/captures/amalur_trim_trigger_20261105T113036.gfxr'
def lz4(raw,expected):
 out=bytearray();i=0
 def length(base):
  nonlocal i
  n=base
  if base==15:
   while True:
    assert i<len(raw);x=raw[i];i+=1;n+=x
    if x!=255:break
  return n
 while i<len(raw):
  token=raw[i];i+=1;n=length(token>>4)
  assert i+n<=len(raw) and len(out)+n<=expected;out+=raw[i:i+n];i+=n
  if i==len(raw):break
  assert i+2<=len(raw);off=raw[i]|raw[i+1]<<8;i+=2;assert 0<off<=len(out)
  n=length(token&15)+4;assert len(out)+n<=expected
  for _ in range(n):out.append(out[-off])
 assert len(out)==expected
 return bytes(out)
want={7496,7499,7502};found={}
with CAP.open('rb') as f:
 sig,version,compression,opts=struct.unpack('<4sIII',f.read(16));f.seek(opts*8,1);index=-1
 while True:
  h=f.read(12)
  if not h:break
  assert len(h)==12;size,kind=struct.unpack('<QI',h);index+=1;start=f.tell();head=f.read(min(size,48))
  if kind&0x7fffffff==3 and len(head)>=48 and struct.unpack_from('<I',head)[0]&0xffff==8:
   meta,thread,device,image,n,aspect,layout,count=struct.unpack('<IQQQQIII',head)
   if image in want:
    levels=struct.unpack('<%dQ'%count,f.read(count*8));packed=f.read(size-48-count*8)
    raw=lz4(packed,n) if kind&0x80000000 else packed
    assert n==len(raw)==sum(levels) and count==1 and n==3072
    tight=raw[:8*8*6*4]
    (OUT/f'image-{image}-init.bin').write_bytes(raw);(OUT/f'image-{image}-tight.rgba').write_bytes(tight)
    found[image]={'image':image,'block_index':index,'file_offset':start,'data_size':n,'stored_size':size,'compressed':bool(kind&0x80000000),'level_sizes':levels,'tight_bytes':len(tight),'sha256':hashlib.sha256(raw).hexdigest(),'tight_sha256':hashlib.sha256(tight).hexdigest(),'first_pixel':list(tight[:4])}
  f.seek(start+size)
assert set(found)==want
assert found[7496]['tight_sha256']=='df71f39a8cfa77673155c7ec5d5de4b3d36583c05c712ac9022e920c96fcef1c'
(OUT/'ambient-image-extraction.json').write_text(json.dumps({'capture':str(CAP),'images':found,'packing':'Tight6RGBA8faces first1536B;level-tail padding1536B. World7496 hash independently matches reviewed prior extraction.'},indent=2))
print(json.dumps(found))
