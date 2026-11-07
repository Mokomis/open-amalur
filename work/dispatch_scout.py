from pathlib import Path
import struct,json,hashlib,sys
root=Path.home()/'Documents'/'Opem Amalur'
sys.path.insert(0,str(root/'tools'/'python-libs'))
import capstone
path=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe')
b=path.read_bytes()
assert hashlib.sha256(b).hexdigest()=='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
pe=struct.unpack_from('<I',b,0x3c)[0]
assert b[pe:pe+4]==b'PE\0\0'
count=struct.unpack_from('<H',b,pe+6)[0]
optsize=struct.unpack_from('<H',b,pe+20)[0]
base=struct.unpack_from('<I',b,pe+24+28)[0]
sections=[]
for i in range(count):
 p=pe+24+optsize+40*i
 name=b[p:p+8].rstrip(b'\0').decode()
 vs,va,sz,off=struct.unpack_from('<IIII',b,p+8)
 sections.append((name,base+va,sz,off))
def raw(va,n):
 for name,start,sz,off in sections:
  if start<=va and va+n<=start+sz:
   return b[off+va-start:off+va-start+n]
 raise ValueError(hex(va))
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
md.detail=True
def dis(va,n):
 return [dict(address=hex(i.address),bytes=i.bytes.hex(),mnemonic=i.mnemonic,operands=i.op_str) for i in md.disasm(raw(va,n),va)]

import re
start=0x1080000;data=raw(start,0x60000);hits=[]
for m in re.finditer(b'\xc1[\xe8-\xef]\x19',data):
 va=start+m.start()
 code=dis(va,96)
 if any(i['mnemonic']=='jmp' and ('ptr' in i['operands'] or i['operands'] in ['eax','ecx','edx','ebx','esi','edi']) for i in code):hits.append({'address':hex(va),'instructions':code})
result={'target_sha256':hashlib.sha256(b).hexdigest(),'scope_start':hex(start),'scope_bytes':len(data),'dispatch_candidates':hits,'reader_calls':[]}
for i in md.disasm(raw(0x10c5df0,0xcc0),0x10c5df0):
 if i.mnemonic=='call':result['reader_calls'].append({'address':hex(i.address),'target':i.op_str})
out=root/'outputs'/'bytecode-reader'/'offline-dispatch-scout.json';out.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'dispatch_candidates':[h['address'] for h in hits],'reader_calls':result['reader_calls']},indent=2))
