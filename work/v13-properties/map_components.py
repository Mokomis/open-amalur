from pathlib import Path
import struct,json,re,sys
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);sys.path.insert(0,str(r/'tools/python-libs'));from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
pseudo=json.loads((r/'outputs/scene-v13/rea-session-live/type_property_factory.json').read_text())['structuredContent']['normalized_result'];rows=[]
for m in re.finditer(r'case (0x[0-9a-f]+|\d+):\s+uVar1 = FUN_([0-9a-f]+)\(6,(0x[0-9a-f]+|\d+)\)',pseudo):
 kind=int(m[1],0);alloc=int(m[2],16);size=int(m[3],0);tables=[]
 for ins in md.disasm(raw(alloc,240),alloc):
  if ins.mnemonic=='ret':break
  if ins.mnemonic!='mov' or not re.match(r'dword ptr \[(eax|edi|esi)\], 0x',ins.op_str):continue
  tab=int(ins.op_str.split(', ')[1],0)
  try:
   col=struct.unpack('<I',raw(tab-4,4))[0];sig,off,cd,td,base=struct.unpack('<5I',raw(col,20));name=raw(td+8,220).split(b'\0')[0].decode('ascii');slots=struct.unpack('<4I',raw(tab,16))
   if sig!=0 or off>4096 or not name.startswith('.?A'):continue
  except (ValueError,UnicodeDecodeError):continue
  tables.append(dict(name=name,table=hex(tab),slots={hex(i*4):hex(x) for i,x in enumerate(slots)}))
 assert len(tables)>=1, f'Missing native table for {kind}'
 getter=int(tables[0]['slots']['0xc'],0)
 instructions=list(md.disasm(raw(getter,8),getter))
 first=instructions[0]
 value=0 if first.mnemonic=='xor' and first.op_str=='eax, eax' else (int(first.op_str.split(', ')[1],0) if first.mnemonic=='mov' and first.op_str.startswith('eax, ') else None)
 assert value==kind and instructions[1].mnemonic=='ret', f'Kind getter differs for {kind}: {first.mnemonic} {first.op_str}'
 rows.append(dict(kind=kind,allocator=hex(alloc),allocation_bytes=size,native_kind_getter_verified=True,tables=tables[:1]))
assert len(rows)==43
(r/'outputs/scene-v13/component-map.json').write_text(json.dumps(dict(native_factory='0xfa3d20',target_sha256='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314',components=rows),indent=2));print(json.dumps(dict(native_component_kinds=len(rows),kind_getters_verified=sum(x['native_kind_getter_verified'] for x in rows))))
