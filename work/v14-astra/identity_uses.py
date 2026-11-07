from pathlib import Path
import re,json,struct
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);import sys
sys.path.insert(0,str(r/'tools/python-libs'));import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
slots=[dict(offset=hex(i*4),address=hex(x)) for i,x in enumerate(struct.unpack('<58I',raw(0x174d554,232)))]
uses=[]
for ins in md.disasm(raw(0xa6bf00,0x7c00),0xa6bf00):
 if '[eax + 0x4c]' in ins.op_str or '[edx + 0x4c]' in ins.op_str or '[ecx + 0x4c]' in ins.op_str:
  uses.append(dict(va=hex(ins.address),instruction=ins.mnemonic+' '+ins.op_str,context=[dict(va=hex(i.address),instruction=i.mnemonic+' '+i.op_str) for i in md.disasm(raw(ins.address-24,72),ins.address-24)]))
const=[]
for pattern in [b'\x68\xb9\x00\x00\x00',b'\x3d\xb9\x00\x00\x00']:
 for m in re.finditer(re.escape(pattern),b):
  a=va(m.start())
  if a:const.append(dict(va=hex(a),bytes=pattern.hex()))
x=dict(extended_slots=slots[44:],virtual_4c_uses=uses,constant185_uses=const);(r/'outputs/scene-v14-astra/identity-uses.json').write_text(json.dumps(x,indent=2));print(json.dumps(x,indent=2))
