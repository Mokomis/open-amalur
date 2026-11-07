from pathlib import Path
import json,re
r=Path.home()/'Documents/Opem Amalur';out=r/'outputs/scene-v08';pairs=dict(l.split('\t') for l in (out/'modules/modules.tsv').read_text().splitlines() if l and not l.startswith('#'))
s=(out/'modules'/pairs['options_win']).read_text().splitlines()
print('\n'.join(s[15990:16320]))
