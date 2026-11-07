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
names=json.loads((root/'outputs'/'bytecode-reader'/'offline-opcode-table.json').read_text())['rows']
targets=struct.unpack('<86I',raw(0x10b0ba4,86*4));endpoints=sorted(set(targets)|{0x10b0ba4})
selected=[0,2,6,7,9,25,27,28,60,67,70,85]
result={'target_sha256':hashlib.sha256(b).hexdigest(),'dispatch_address':'0x10add57','table_address':'0x10b0ba4','scope':'on-disk interpreter variant A, entry reachability not established','targets':[],'selected_handlers':[],'entry_prefix':dis(0x10adc00,0x140)}
for op,va in enumerate(targets):
 result['targets'].append({'opcode':op,'name':names[op]['name'],'target':hex(va)})
 if op in selected:
  end=next((v for v in endpoints if v>va),va+512)
  result['selected_handlers'].append({'opcode':op,'name':names[op]['name'],'address':hex(va),'end':hex(end),'instructions':dis(va,min(end-va,4096))})
out=root/'outputs'/'bytecode-reader'/'offline-vm-handlers.json';out.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result['targets'],indent=2))
