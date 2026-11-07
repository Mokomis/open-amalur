from pathlib import Path
import platform,json,hashlib,time
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';base=r/'outputs/initial-corpus-drafts-v05';matches=[];total=0;files=0;start=time.monotonic()
for p in base.glob('scripts/*/whole-script.lua'):
 n=p.stat().st_size;total+=n;files+=1
 if total>8*1024**3 or n>64*1024**2:raise ValueError('corpus source search bound exceeded')
 b=p.read_bytes();needle=b'__getfenv(1)["parent"] =';at=b.find(needle)
 if at>=0:matches.append({'file':str(p),'source_sha256':hashlib.sha256(b).hexdigest(),'offset':at,'context':b[max(0,at-180):at+250].decode('utf8')})
index=json.loads((r/'outputs/scene-v07/standalone-name-index.json').read_text(encoding='utf-8-sig'))
for m in matches:
 digest=Path(m['file']).parent.name;m['input_sha256']=digest;m['names']=[x for x in index if x['sha256']==digest]
j={'files':files,'source_bytes':total,'seconds':time.monotonic()-start,'matches':matches};(r/'outputs/scene-v08/parent-definition-search.json').write_text(json.dumps(j,indent=2));print(json.dumps(j,indent=2))
