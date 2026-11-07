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

def fileva(off):
 for name,start,sz,raw_off in sections:
  if raw_off<=off<raw_off+sz:return start+off-raw_off
 return None
result={'target_sha256':hashlib.sha256(b).hexdigest(),'reader_entry':dis(0x10c5df0,0x300),'opcode_strings':[]}
for text in [b'GETGLOBAL_MEM',b'GETFIELD_R1',b'LOADK',b'BytecodeLoader',b'bad header']:
 start=0
 while True:
  offset=b.find(text,start)
  if offset<0:break
  va=fileva(offset)
  item={'text':text.decode(),'offset':hex(offset),'va':hex(va) if va else None}
  if va:
   needle=struct.pack('<I',va);refs=[];pos=0
   while True:
    pos=b.find(needle,pos)
    if pos<0:break
    refs.append({'offset':hex(pos),'va':hex(fileva(pos)) if fileva(pos) else None});pos+=1
   item['pointer_refs']=refs[:80]
  result['opcode_strings'].append(item);start=offset+1
out=root/'outputs'/'bytecode-reader';out.mkdir(parents=True,exist_ok=True)
(out/'offline-reader-scout.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result['opcode_strings'],indent=2))
