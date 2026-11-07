from pathlib import Path
import struct,json
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);table=0x172fcf8;col=struct.unpack('<I',raw(table-4,4))[0];td=struct.unpack('<5I',raw(col,20))[3]
report=dict(table=hex(table),name=raw(td+8,200).split(b'\0')[0].decode('ascii'),refs=[hex(x) for x in refs(table)],slots=[hex(x) for x in struct.unpack('<8I',raw(table,32))])
(r/'outputs/scene-v15/batch-request-rtti.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
