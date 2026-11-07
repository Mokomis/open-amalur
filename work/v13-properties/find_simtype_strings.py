from pathlib import Path
import re,json
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);rows=[]
for m in re.finditer(rb'[\x20-\x7e]{6,600}',b):
 text=m.group().decode('ascii')
 if not any(x in text.lower() for x in ['simtype','type.cpp','partblueprint','type_bxml','compact','bitreader','bitstream','partset']):continue
 rows.append(dict(text=text,va=hex(va(m.start())) if va(m.start()) else None))
(r/'outputs/scene-v13/simtype-strings.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
