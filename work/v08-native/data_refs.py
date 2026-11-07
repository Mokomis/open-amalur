from pathlib import Path
import struct,json,hashlib
root=Path.home()/'Documents'/'Opem Amalur';b=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe').read_bytes();assert hashlib.sha256(b).hexdigest()=='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
pe=struct.unpack_from('<I',b,0x3c)[0];count=struct.unpack_from('<H',b,pe+6)[0];opt=struct.unpack_from('<H',b,pe+20)[0];secs=[]
for i in range(count):
 p=pe+24+opt+i*40;vs,rva,size,off=struct.unpack_from('<IIII',b,p+8);secs.append((0x400000+rva,size,off))
def va(off):
 for a,n,o in secs:
  if o<=off<o+n:return a+off-o
 return None
def raw(a,n):
 for s,z,o in secs:
  if s<=a and a+n<=s+z:return b[o+a-s:o+a-s+n]
 raise ValueError(a)
def refs(word):
 pat=struct.pack('<I',word);at=b.find(pat)
 while at>=0:
  a=va(at)
  if a:yield a
  at=b.find(pat,at+1)
import sys
result=[]
for text in sys.argv[1:]:
 value=int(text,0);result.append({'target':hex(value),'refs':[{'address':hex(a),'raw_around':raw(a-16,64).hex()} for a in list(refs(value))[:100]]})
(root/'outputs/scene-v08/data-refs.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
