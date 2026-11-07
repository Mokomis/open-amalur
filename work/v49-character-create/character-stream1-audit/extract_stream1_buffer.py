"""Extract only the three active ambient InitImage payloads, no replay/GPU."""
from pathlib import Path
import struct,json,hashlib
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
OUT=ROOT/'work/v49-character-create/character-stream1-audit'
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

records=[];rawbuffer=None
with CAP.open('rb') as f:
 sig,version,compression,opts=struct.unpack('<4sIII',f.read(16));f.seek(opts*8,1);index=-1
 while True:
  h=f.read(12)
  if not h:break
  size,kind=struct.unpack('<QI',h);index+=1;start=f.tell()
  if index>=76331:break
  head=f.read(min(size,36))
  if kind&0x7fffffff==3 and len(head)>=36:
   mt,thread,device,object,n=struct.unpack('<IQQQQ',head)
   if mt&0xffff==7 and object==1831:
    packed=f.read(size-36);raw=lz4(packed,n) if kind&0x80000000 else packed;assert len(raw)==n==131072
    rawbuffer=raw
    records.append({'kind':'InitBuffer','index':index,'meta':mt,'device':device,'buffer':object,'bytes':n,'stored_size':size,'file_offset':start,'sha256':hashlib.sha256(raw).hexdigest()})
   if mt&0xffff==2:
    mem=device;off=object
    if mem==1832:
     packed=f.read(size-36);raw=lz4(packed,n) if kind&0x80000000 else packed;assert len(raw)==n
     records.append({'kind':'FillMemory','index':index,'meta':mt,'memory':mem,'offset':off,'bytes':n,'stored_size':size,'file_offset':start,'sha256':hashlib.sha256(raw).hexdigest()})
  f.seek(start+size)
assert rawbuffer is not None
(OUT/'native-stream1-buffer1831.bin').write_bytes(rawbuffer)
from collections import Counter
out={'capture':str(CAP),'records_before_submit76331':records,'buffer_byte_counts':dict(Counter(rawbuffer)),'first96bytes_hex':rawbuffer[:96].hex(),'first8records_stride12':[rawbuffer[i*12:i*12+12].hex() for i in range(8)],'first8records_stride8':[rawbuffer[i*8:i*8+8].hex() for i in range(8)]}
(OUT/'buffer1831-content.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
