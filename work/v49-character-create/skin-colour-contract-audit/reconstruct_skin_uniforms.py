"""Extract only the three active ambient InitImage payloads, no replay/GPU."""
from pathlib import Path
import struct,json,hashlib
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
OUT=ROOT/'work/v49-character-create/skin-colour-contract-audit'
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

targets={67663:(919680,919936),67691:(951488,951744)};found=[];result={}
with CAP.open('rb') as f:
 _,_,_,opts=struct.unpack('<4sIII',f.read(16));f.seek(opts*8,1);idx=-1
 while True:
  h=f.read(12)
  if not h:break
  size,kind=struct.unpack('<QI',h);idx+=1;start=f.tell()
  if idx>=76331:break
  head=f.read(min(size,36))
  if kind&0x7fffffff==3 and len(head)==36 and struct.unpack_from('<I',head)[0]&0xffff==2:
   _,thread,mem,off,n=struct.unpack('<IQQQQ',head)
   if mem==52 and off==0 and n>=952000:
    packed=f.read(size-36);raw=lz4(packed,n) if kind&0x80000000 else packed
    assert len(raw)==n
    found.append({'event':idx,'file_offset':start,'memory':mem,'offset':off,'bytes':n,'sha256':hashlib.sha256(raw).hexdigest()})
    for draw,(mat,inst) in targets.items():
     cb0=raw[mat:mat+80];cb3=raw[inst:inst+144]
     assert cb0==(ROOT/'work/v33-native-camera/memory-52-prefix.bin').read_bytes()[mat:mat+80]
     assert cb3==(ROOT/'work/v33-native-camera/memory-52-prefix.bin').read_bytes()[inst:inst+144]
     (OUT/f'draw-{draw}-materialCB.bin').write_bytes(cb0);(OUT/f'draw-{draw}-instanceCB.bin').write_bytes(cb3)
     result[draw]={'material_offset':mat,'instance_offset':inst,'material20':struct.unpack('<20f',cb0),'skinColor':struct.unpack_from('<4f',cb3,32),'cb0_sha256':hashlib.sha256(cb0).hexdigest(),'cb3_sha256':hashlib.sha256(cb3).hexdigest()}
  f.seek(start+size)
assert result
out={'submission_event':76331,'command_buffer':46,'host_fills_before_submission':found,'selected_draws':result,'prior_prefix_matches':True}
(OUT/'skin-uniform-temporal-proof.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
