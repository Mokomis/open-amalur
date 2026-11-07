from pathlib import Path
import json
r=Path.home()/'Documents/Opem Amalur';out=r/'outputs/scene-v08';pairs=dict(l.split('\t') for l in (out/'modules/modules.tsv').read_text().splitlines() if l and not l.startswith('#'))
for name in ['Constants','SpaceCommon','main_menu','common_tools']:
 s=(out/'modules'/pairs[name]).read_text().splitlines();loads=[]
 for i,l in enumerate(s):
  if 'value = "' in l:loads.append((i+1,l.strip()))
 print(name,'\n',loads[:65])
