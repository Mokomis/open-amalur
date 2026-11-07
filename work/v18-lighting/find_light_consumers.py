"""Bounded original PE x86 inventory: exact source record stride and Space fields."""
from pathlib import Path
import json,platform,sys
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);sys.path.insert(0,str(r/'tools/python-libs'))
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32);matches=[]
region=raw(0xc70000,0xd40000-0xc70000)
import re
for m in re.finditer(rb'\x6b[\xc0-\xff]\x6c|\x69[\xc0-\xff]\x6c\x00\x00\x00|\x83[\xc0-\xc7]\x6c',region):
 address=0xc70000+m.start();start=region.rfind(b'\xcc\xcc',max(0,m.start()-768),m.start());begin=0xc70000+start+2 if start>=0 else address-48
 rows=list(md.disasm(raw(begin,address-begin+120),begin))
 if not any(i.address==address and i.mnemonic in ['imul','add']for i in rows):continue
 matches.append(dict(address=hex(address),entry_candidate=hex(begin),context=[dict(address=hex(i.address),mnemonic=i.mnemonic,operands=i.op_str)for i in rows]))
(r/'outputs/scene-v18/lighting-consumer-candidates.json').write_text(json.dumps(matches,indent=2))
print(json.dumps([dict(address=x['address'],entry=x['entry_candidate'],calls=[i['operands']for i in x['context']if i['mnemonic']=='call'])for x in matches]))
