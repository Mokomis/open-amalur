from pathlib import Path
import json
r=Path.home()/'Documents/Opem Amalur';out=r/'outputs/scene-v08';index=json.loads((r/'outputs/scene-v07/standalone-name-index.json').read_text(encoding='utf-8-sig'))
for name in ['ParentUtils','Fate_Shift_Start']:
 print(name,json.dumps([x for x in index if x.get('name')==name]))
j=json.loads((out/'modules/module-inventory.json').read_text());print('currentselected',[(x['module'],x['source_file']) for x in j['modules'] if x['module'] in ['ParentUtils','Fate_Shift_Start']])
