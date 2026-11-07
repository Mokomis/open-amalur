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

import re
rows=[]
for m in re.finditer(rb'\.\?A[UV][ -~]{1,180}?\x00',b):
 name=m.group()[:-1].decode('ascii')
 if not any(x.lower() in name.lower() for x in ['Material','Shader','VertexBuffer','Texture']):continue
 address=va(m.start())
 if address is None:continue
 td=address-8
 tables=[]
 for ref in refs(td):
  col=ref-12
  if col%4:continue
  try:data=struct.unpack('<5I',raw(col,20))
  except ValueError:continue
  if data[0] or data[1]>4096:continue
  for vref in refs(col):
   if vref%4:continue
   table=vref+4
   try:slots=struct.unpack('<20I',raw(table,20*4))
   except ValueError:continue
   tables.append({'col':hex(col),'offset':data[1],'vtable':hex(table),'slots':[hex(v) for v in slots],
      'slot9_bytes':raw(slots[9],32).hex() if any(a<=slots[9]<a+n-32 for a,n,o in secs) else None})
 rows.append({'name':name,'type_descriptor':hex(td),'vtables':tables})
out=root/'outputs/scene-v09/render-rtti.json';out.write_text(json.dumps(rows,indent=2))
print(json.dumps([{'name':r['name'],'tables':len(r['vtables'])} for r in rows],indent=2))
