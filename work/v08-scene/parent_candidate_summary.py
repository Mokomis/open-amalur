from pathlib import Path
import json
r=Path.home()/'Documents/Opem Amalur';j=json.loads((r/'outputs/scene-v08/parent-candidates.json').read_text())
rows=[]
for m in j['matches']:
 sites=[x for x in m['occurrences'] if 'SETFIELD' in x['context'] or 'LOADK' in x['context'].split('"parent"')[0] or '__getfenv(1)["parent"] =' in x['context']]
 if sites:rows.append({'file':m['file'],'names':m['names'],'sites':sites})
print(json.dumps(rows,indent=2))
for name in ['initial-corpus-drafts-v05/validation.json','initial-corpus-v04/inventory.json']:
 p=r/'outputs'/name;j=json.loads(p.read_text());print(name,list(j.keys()))
