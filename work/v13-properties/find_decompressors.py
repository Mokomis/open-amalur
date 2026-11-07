from pathlib import Path
import re,json,struct
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')]);rows=[]
for m in re.finditer(rb'\.\?A[UV][^\x00]{1,500}',b):
 name=m.group().decode('ascii','replace')
 if not any(t.lower() in name.lower() for t in ['decompress','bxml','xml','serialize','assetbundle','bundledecomp']):continue
 rows.append(dict(name=name,va=hex(va(m.start()))))
(r/'outputs/scene-v13/decompressor-rtti.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
