from pathlib import Path
r=Path.home()/'Documents/Opem Amalur';out=r/'outputs/scene-v08';pairs=dict(l.split('\t') for l in (out/'modules/modules.tsv').read_text().splitlines() if l and not l.startswith('#'));s=(out/'modules'/pairs['Constants']).read_text().splitlines()
print('\n'.join(s[-260:]));print('SPECIAL',[(i+1,l) for i,l in enumerate(s) if any(x in l for x in ['setmetatable','make_read_only','__index','__newindex'])])
