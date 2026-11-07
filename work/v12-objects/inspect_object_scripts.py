from pathlib import Path
import re,json
r=Path.home()/'Documents/Opem Amalur';index=json.loads((r/'outputs/scene-v07/standalone-name-index.json').read_text(encoding='utf-8-sig'));rows=[]
for entry in index:
 if str(entry.get('name','')).lower() not in ['workbench','loaddoor','smashable_dropgold','chest']:continue
 p=r/'outputs/initial-corpus-drafts-v05/scripts'/entry['sha256']/'whole-script.lua';s=p.read_text();globals=sorted(set(re.findall(r'__getfenv\(1\)\["([^"]+)"\]',s)));keys=sorted(set(re.findall(r'\["([A-Za-z_][A-Za-z0-9_]*)"\]',s)))
 row=dict(name=entry['name'],source=str(p),input_sha256=entry['sha256'],bytes=len(s),globals=globals,keys=keys,tail=s[-1800:]);rows.append(row)
(r/'outputs/scene-v12/object-script-survey.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
