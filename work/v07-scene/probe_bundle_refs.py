from pathlib import Path
from collections import Counter
import re,struct,json
root=Path.home()/'Documents'/'Opem Amalur';idx={};ext=Counter()
for n in ['initial','DATA','patch']:
 d=(root/f'outputs/{n}-archive-list.txt').read_bytes();t=d.decode('utf-16' if d.startswith(b'\xff\xfe') else 'utf-8-sig')
 for line in t.splitlines():
  name=line.strip();m=re.fullmatch(r'(\d+)(?:_\d+)?\.(\w+)',name)
  if m:idx.setdefault(int(m[1]),set()).add(name);ext[m[2]]+=1
print('extensions',ext)
for name in ['524859.bundle','524912.bundle']:
 d=(root/'work/scene-inputs-v07/initial_0.pak'/name).read_bytes();n=struct.unpack_from('<I',d,8)[0];vals=struct.unpack_from('<'+str(n)+'I',d,16);rows=[]
 for v in vals:
  names=sorted(idx.get(v,[]));types={p.split('.',1)[1] for p in names}
  if any(s not in ['dds','tex_bxml','material_bxml','mtl_bxml'] for s in types) or not names:rows.append({'id':v,'files':names})
 out={'file':name,'candidate_count':n,'records':rows};(root/f'outputs/scene-v07/{name}-refs.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
