from pathlib import Path
import re,json
r=Path.home()/'Documents/Opem Amalur';base=r/'references';rows=[];seen=0
for repo in ['DevCortez--KoaModFramework','hardkiller2565123123--Kingdoms-of-Amalur-Re-Reckoning-coop-mod','Kender2--amalur','mburbea--ModelSwapper']:
 for p in (base/repo).rglob('*'):
  if not p.is_file() or p.suffix.lower() not in ['.cs','.cpp','.h','.hpp','.lua','.md'] or p.stat().st_size>2*1024*1024:continue
  if any(x in ['.git','node_modules','third_party','external','packages','bin','obj'] for x in p.relative_to(base/repo).parts):continue
  b=p.read_bytes();seen+=len(b)
  if seen>256*1024*1024:raise ValueError('Reference search byte bound')
  s=b.decode('utf-8',errors='replace')
  for i,line in enumerate(s.splitlines()):
   if re.search(r'sim.?type|property.?reader|property.?set',line,re.I):rows.append(dict(file=str(p.relative_to(base)),line=i+1,text=line.strip()[:180]))
(r/'outputs/scene-v13/reference-search.json').write_text(json.dumps(dict(bytes=seen,matches=rows),indent=2));print(json.dumps(dict(bytes=seen,count=len(rows),matches=rows[:35]),indent=2))
