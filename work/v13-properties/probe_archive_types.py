from pathlib import Path
import collections,json,re
r=Path.home()/'Documents/Opem Amalur'
for name in ['initial-archive-list.txt','DATA-archive-list.txt','patch-archive-list.txt']:
 data=(r/'outputs'/name).read_bytes();s=data.decode('utf-16' if data.startswith(b'\xff\xfe') else 'utf-8-sig');names=[x.strip() for x in s.splitlines()];cnt=collections.Counter(x.split('.',1)[-1] for x in names if '.' in x);print(name,json.dumps({k:v for k,v in cnt.items() if any(x in k for x in ['type','bundle','part','cache'])}));print([x for x in names if 'simtype_mgr' in x])
for repo in ['atom0s--depak','DevCortez--KoaModFramework']:
 for f in (r/'references'/repo).rglob('*'):
  if f.suffix not in ['.cpp','.h','.hpp','.py','.cs']:continue
  for i,line in enumerate(f.read_text(errors='replace').splitlines(),1):
   if any(x in line.lower() for x in ['simtype','0xb9','0x94']):print(str(f.relative_to(r)),i,line[:200])
