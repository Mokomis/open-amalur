"""Preserve v0.8 sources and add authored v0.9 changes, excluding private assets."""
from pathlib import Path
import platform,zipfile,json,hashlib,shutil
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';o=r/'outputs/scene-v09';source=r/'outputs/opem-amalur-scene-source-v0.9.zip';evidence=r/'outputs/opem-amalur-scene-evidence-v0.9.zip'
allowed={'.c','.h','.lua','.py','.txt','.cmake','.xml','.cmd','.ps1','.patch','.md','.json'}
selected={}
for folder in ['v09-host','v09-collision','v09-textures','v09-scene']:
 base=r/'work'/folder
 for p in base.rglob('*'):
  rel=p.relative_to(base)
  if not p.is_file() or any(x.startswith('build-') or x in ['references','__pycache__','materials-initial'] for x in rel.parts):continue
  if p.suffix not in allowed and p.name!='CMakeLists.txt':continue
  # Native evidence and game-derived geometry receipts belong in evidence, not authored sources.
  if p.suffix=='.json' and 'profile' not in p.name:continue
  selected[p.relative_to(r).as_posix()]=p
for name in ['amalur_blob.py','amalur_shell.py','amalur_scene.py']:
 p=r/'work/v07-bxml'/name;selected[p.relative_to(r).as_posix()]=p
with zipfile.ZipFile(r/'outputs/opem-amalur-scene-source-v0.8.zip') as old,zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for info in old.infolist():
  if info.filename in selected:continue
  z.writestr(info,old.read(info.filename))
 for rel,p in sorted(selected.items()):
  z.write(p,rel);dest=r/'src/scene-v09'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 z.write(o/'PROGRESS.txt','V09_PROGRESS.txt');z.write(r/'work/v09-scene/BUILDING.txt','V09_BUILDING.txt')
with zipfile.ZipFile(evidence,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in o.rglob('*'):
  if p.is_file() and p.suffix in ['.json','.txt','.log','.png']:z.write(p,p.relative_to(o).as_posix())
records=[]
for p in [source,evidence,o/'opem-amalur-scene-v0.9-arm64.apk']:
 records.append(dict(file=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(r/'outputs/v09-package-sha256.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
