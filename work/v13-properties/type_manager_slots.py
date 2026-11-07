from pathlib import Path
import struct,json
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);table=0x174d554
slots=struct.unpack('<48I',raw(table,192));result=[dict(offset=hex(i*4),address=hex(x),prefix=raw(x,12).hex() if any(a<=x<a+n-12 for a,n,o in secs) else None) for i,x in enumerate(slots)];(r/'outputs/scene-v13/type-manager-slots.json').write_text(json.dumps(result,indent=2));print(json.dumps(result[18:45],indent=2))
