from pathlib import Path
import re,json
from collections import Counter
root=Path.home()/'Documents'/'Opem Amalur';rows=[];counts=Counter()
for n in ['DATA','initial','patch']:
 d=(root/f'outputs/{n}-archive-list.txt').read_bytes();t=d.decode('utf-16' if d.startswith(b'\xff\xfe') else 'utf-8-sig')
 for line in t.splitlines():
  name=line.strip()
  if not re.fullmatch(r'\d+(?:_\d+)?\.\w+',name):rows.append({'archive':n,'file':name});counts[name.rsplit('.',1)[-1]]+=1
(root/'outputs/scene-v07/unmatched-archive-names.json').write_text(json.dumps(rows,indent=2));print(counts);print(rows[:35])
