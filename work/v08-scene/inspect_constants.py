from pathlib import Path
import json
r=Path.home()/'Documents/Opem Amalur';out=r/'outputs/scene-v08';pairs=dict(l.split('\t') for l in (out/'modules/modules.tsv').read_text().splitlines() if l and not l.startswith('#'))
print('constant modules',[(k,v) for k,v in pairs.items() if 'constant' in k.lower()])
s=(out/'modules'/pairs['main_menu']).read_text().splitlines();print('\n'.join(s[660:735]));print('\n'.join(s[:130]));
for k,v in pairs.items():
 if 'constant' in k.lower():print(k,'\n'.join((out/'modules'/v).read_text().splitlines()[:75]))
