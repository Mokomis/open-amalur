from pathlib import Path
import sys,json,re
sys.argv=sys.argv[:1]
exec((Path(__file__).parent/'data_refs.py').read_text().split('import sys\nresult=[]')[0])
rows=[]
for m in re.finditer(rb'[\x20-\x7e]{3,}\x00',b):
 if b'parent' in m.group().lower():
  rows.append({'address':hex(va(m.start())),'text':m.group()[:-1].decode('ascii')})
(root/'outputs/scene-v08/parent-raw-strings.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
