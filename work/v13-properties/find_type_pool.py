from pathlib import Path
import json,struct
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')])
rows=[]
for pattern,label in [(b'\xa3'+struct.pack('<I',0x19fec38),'store eax to type manager'),(b'\x89\x0d'+struct.pack('<I',0x19fec38),'store ecx to type manager'),(b'\x89\x35'+struct.pack('<I',0x19fec38),'store esi to type manager')]:
 at=b.find(pattern)
 while at>=0:
  a=va(at)
  if a:rows.append(dict(kind=label,address=hex(a),raw_before=raw(a-80,112).hex()))
  at=b.find(pattern,at+1)
refs2238=list(refs(0x2238));o=dict(manager='0x19fec38',pool_offset='0x2238',writers=rows,pool_offset_matches=[hex(x) for x in refs2238[:100]],total_pool_offset_matches=len(refs2238));(r/'outputs/scene-v13/type-pool-locations.json').write_text(json.dumps(o,indent=2));print(json.dumps(o,indent=2))
