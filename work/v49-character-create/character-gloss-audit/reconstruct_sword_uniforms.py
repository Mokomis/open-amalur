"""Extract only the three active ambient InitImage payloads, no replay/GPU."""
from pathlib import Path
import struct,json,hashlib
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
OUT=ROOT/'work/v49-character-create/character-gloss-audit'
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

begin,end=651264,651776;window=bytearray(end-begin);written=bytearray(end-begin);fills=[]
with CAP.open('rb') as f:
 sig,version,compression,opts=struct.unpack('<4sIII',f.read(16));f.seek(opts*8,1);index=-1
 while True:
  h=f.read(12)
  if not h:break
  size,kind=struct.unpack('<QI',h);index+=1;start=f.tell()
  if index>=76331:break
  head=f.read(min(size,36))
  if kind&0x7fffffff==3 and len(head)>=36 and struct.unpack_from('<I',head)[0]&0xffff==2:
   meta,thread,mem,off,n=struct.unpack('<IQQQQ',head)
   if mem==52 and off<end and begin<off+n:
    packed=f.read(size-36);raw=lz4(packed,n) if kind&0x80000000 else packed;assert len(raw)==n
    lo=max(begin,off);hi=min(end,off+n);window[lo-begin:hi-begin]=raw[lo-off:hi-off];written[lo-begin:hi-begin]=b'\1'*(hi-lo)
    fills.append({'index':index,'file_offset':start,'memory':mem,'offset':off,'bytes':n,'stored_size':size,'compressed':bool(kind&0x80000000),'intersected_range':[lo,hi],'uncompressed_sha256':hashlib.sha256(raw).hexdigest()})
  f.seek(start+size)
assert all(written)
prefix=(ROOT/'work/v33-native-camera/memory-52-prefix.bin').read_bytes()[begin:end]
assert bytes(window)==prefix
(OUT/'draw67406-cb0.bin').write_bytes(window[:64]);(OUT/'draw67406-world-cb68.bin').write_bytes(window[256:])
out={'capture':str(CAP),'draw':67406,'memory':52,'reconstructed_range':[begin,end],'fills_applied_before_submission':fills,'submission_event':76331,'command_buffer':46,'temporal_note':'Draw67406 is recorded before host writes; GPU execution occurs at QueueSubmit76331, so use final intersecting FillMemory before this actual submission.','matches_prior_prefix_all512bytes':True,'cb0_16f':struct.unpack_from('<16f',window),'world_16f':struct.unpack_from('<16f',window,256),'cb0_sha256':hashlib.sha256(window[:64]).hexdigest(),'world_cb256_sha256':hashlib.sha256(window[256:]).hexdigest()}
(OUT/'uniform-temporal-proof.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
