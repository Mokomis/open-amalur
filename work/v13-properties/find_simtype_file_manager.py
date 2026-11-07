from pathlib import Path
import struct,json
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);rows=[]
for value in [0x94,0xb9]:
 pattern=b'\xb8'+struct.pack('<I',value)+b'\xc3';at=b.find(pattern)
 while at>=0:
  address=va(at)
  if address:
   for ref in refs(address):
    table=ref-0x4c
    try:
     col=struct.unpack('<I',raw(table-4,4))[0];sig,offset,cd,td,parent=struct.unpack('<5I',raw(col,20));name=raw(td+8,180).split(b'\0')[0].decode('ascii')
     if sig or offset>4096 or not name.startswith('.?A'):continue
     slots=struct.unpack('<44I',raw(table,176))
    except (ValueError,UnicodeDecodeError):continue
    rows.append(dict(file_type=value,function=hex(address),table=hex(table),name=name,slots={hex(i*4):hex(x) for i,x in enumerate(slots)}))
  at=b.find(pattern,at+1)
(r/'outputs/scene-v13/simtype-file-managers.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
