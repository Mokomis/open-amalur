"""Windows static PE-only focused Formula RTTI/constructor lookup."""
from pathlib import Path
import json, struct, re, sys, platform
assert platform.system() == 'Windows'
r = Path.home() / 'Documents/Opem Amalur'
base_source = (r / 'work/v09-scene/render_rtti.py').read_text()
exec(base_source[:base_source.index('\nimport re')])
sys.path.insert(0, str(r / 'tools/python-libs'))
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32)
def dis(a,n): return [dict(address=hex(i.address), mnemonic=i.mnemonic, operands=i.op_str, bytes=i.bytes.hex()) for i in md.disasm(raw(a,n),a)]
result = []
for name in [b'.?AVPartFormula@BHG@@\0', b'.?AVPartFormulaBlueprint@BHG@@\0']:
    off = b.find(name)
    if off < 0: continue
    td = va(off)-8
    for ref in refs(td):
        col = ref-12
        if col%4: continue
        try: words = struct.unpack('<5I',raw(col,20))
        except ValueError: continue
        if words[0] or words[1] > 4096: continue
        for vref in refs(col):
            if vref%4: continue
            table = vref+4
            slots = struct.unpack('<24I',raw(table,96))
            stores = []
            for loc in refs(table):
                before = raw(loc-2,2)
                if before[0] != 0xc7: continue
                stores.append(dict(address=hex(loc-2), instructions=dis(loc-2,240)))
            result.append(dict(name=name[:-1].decode(), table=hex(table), slots=[hex(v) for v in slots], stores=stores[:12]))
out = r / 'outputs/scene-v16-alchemy/formula-ctor-audit.json'
out.write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps([dict(name=x['name'],table=x['table'], stores=[s['address'] for s in x['stores']]) for x in result]))
