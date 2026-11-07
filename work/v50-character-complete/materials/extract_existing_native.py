"""Read-only narrow extraction from the previously recorded original frame."""
from pathlib import Path
import struct,json,hashlib,subprocess
R=Path(r'C:\Users\rwill\Documents\Opem Amalur');D=Path(__file__).resolve().parent/'evidence'
want={381,382,394,417,418,429,430,975,976}
events={}
for ln,l in enumerate((R/'work/v33-native-camera/dalentarth.jsonl').open()):
 if not ln:continue
 j=json.loads(l);f=j.get('vkFunc',{});a=f.get('args',{})
 if f.get('name')=='vkCreateShaderModule' and a.get('pShaderModule') in want:events[j['index']]=(a['pShaderModule'],a['pCreateInfo']['codeSize'])
def lz4(b,n):
 o=bytearray();i=0
 while i<len(b):
  t=b[i];i+=1;l=t>>4
  if l==15:
   while 1:
    z=b[i];i+=1;l+=z
    if z!=255:break
  o+=b[i:i+l];i+=l
  if i==len(b):break
  back=int.from_bytes(b[i:i+2],'little');i+=2;l=t&15
  if l==15:
   while 1:
    z=b[i];i+=1;l+=z
    if z!=255:break
  for _ in range(l+4):o.append(o[-back])
 assert len(o)==n;return bytes(o)
ans=[]
capture=R/'work/v31-native-slice/captures/amalur_trim_trigger_20261105T113036.gfxr'
with capture.open('rb') as f:
 _,_,_,n=struct.unpack('<4sIII',f.read(16));f.seek(n*8,1);idx=0
 while h:=f.read(12):
  size,kind=struct.unpack('<QI',h);off=f.tell()
  if idx in events:
   b=f.read(size);q=lz4(b[20:],struct.unpack_from('<Q',b,12)[0]) if kind&0x80000000 else b[12:];module,n=events[idx];assert q[60:64]==b'\x03\x02\x23\x07';raw=q[60:60+n];assert struct.unpack_from('<Q',q,len(q)-12)[0]==module
   p=D/f'module-{module}.spv';p.write_bytes(raw);subprocess.run([str(R/'tools/android/android-ndk-r30/shader-tools/windows-x86_64/spirv-dis.exe'),str(p),'-o',str(p.with_suffix('.spvasm'))],check=True)
   ans.append(dict(module=module,event=idx,file_offset=off,bytes=n,sha256=hashlib.sha256(raw).hexdigest()))
  else:f.seek(size,1)
  if idx>=max(events):break
  idx+=1
(D/'module-extraction-receipt.json').write_text(json.dumps(dict(capture=str(capture),capture_sha256='72c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209',modules=ans),indent=2),encoding='utf-8')
print(ans)
