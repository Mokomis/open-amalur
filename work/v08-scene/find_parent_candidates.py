from pathlib import Path
import platform,json,hashlib,time
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';base=r/'outputs/initial-corpus-drafts-v05';matches=[]
index=json.loads((r/'outputs/scene-v07/standalone-name-index.json').read_text(encoding='utf-8-sig'));bynames={}
for x in index:bynames.setdefault(x['sha256'],[]).append(x.get('name'))
for p in base.glob('scripts/*/whole-script.lua'):
 b=p.read_bytes();needle=b'"parent"';at=b.find(needle)
 if at>=0:
  locations=[]
  while at>=0:
   locations.append({'offset':at,'context':b[max(0,at-180):at+150].decode('utf8')});at=b.find(needle,at+1)
  matches.append({'file':str(p),'names':bynames.get(p.parent.name),'occurrences':locations})
j={'candidate_files':len(matches),'matches':matches};(r/'outputs/scene-v08/parent-candidates.json').write_text(json.dumps(j,indent=2));print(json.dumps(j,indent=2))
game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning')
print('LooseLua',list(map(str,game.rglob('*.lua'))))
