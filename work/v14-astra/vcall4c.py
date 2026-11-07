from pathlib import Path
import re,json,struct,sys
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);sys.path.insert(0,str(r/'tools/python-libs'));import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32);hits=[]
for m in re.finditer(rb'\x8b[\x40-\x7f]\x4c',b):
 a=va(m.start())
 if not a or not 0x400000<a<0x1250000:continue
 ins=list(md.disasm(raw(a,40),a))
 if not ins or len(ins[0].bytes)!=3:continue
 dst=ins[0].op_str.split(',')[0]
 if not any(i.mnemonic=='call' and i.op_str==dst for i in ins[1:8]):continue
 before=list(md.disasm(raw(a-24,64),a-24));hits.append(dict(va=hex(a),context=[hex(i.address)+' '+i.mnemonic+' '+i.op_str for i in before]))
(r/'outputs/scene-v14-astra/vcall4c.json').write_text(json.dumps(hits,indent=2));print(json.dumps(hits,indent=2))
