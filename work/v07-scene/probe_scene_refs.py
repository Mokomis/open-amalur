from pathlib import Path
import struct,json,re
root=Path.home()/'Documents'/'Opem Amalur';idx={}
for n in ['initial','DATA','patch']:
 d=(root/f'outputs/{n}-archive-list.txt').read_bytes();t=d.decode('utf-16' if d.startswith(b'\xff\xfe') else 'utf-8-sig')
 for line in t.splitlines():
  m=re.fullmatch(r'(\d+)\.(\w+)',line.strip())
  if m:idx.setdefault(int(m[1]),set()).add(m[2])
for name in ['524859.space_bxml','524912.region_bxml']:
 d=(root/'work/scene-inputs-v07/DATA_0.pak'/name).read_bytes();rows=[]
 for o in range(0,min(len(d),552),4):
  v=struct.unpack_from('<I',d,o)[0]
  if v in idx:rows.append({'file_offset':o,'payload_offset':o-8,'value':v,'types':sorted(idx[v])})
 out={'file':name,'bytes':len(d),'head':d[:80].hex(),'references':rows};(root/f'outputs/scene-v07/{name}-root-refs.json').write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
