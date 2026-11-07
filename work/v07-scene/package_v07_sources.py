"""Preserve authored sources and validation evidence without altering v0.6."""
from pathlib import Path
import platform,json,hashlib,zipfile,shutil
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur';out=root/'outputs/scene-v07'
source=root/'outputs/opem-amalur-scene-source-v0.7.zip';evidence=root/'outputs/opem-amalur-scene-evidence-v0.7.zip'
selected=[]
for name in ['v07-host','v07-portable']:
 base=root/'work'/name
 for p in base.rglob('*'):
  if not p.is_file() or any(part.startswith('build-') or part=='__pycache__' for part in p.relative_to(base).parts):continue
  if p.suffix in ['.log','.exe','.obj','.pdb','.ilk','.lib','.so','.a']:continue
  selected.append(p)
for name in ['v07-bxml','v07-mesh','v07-scripts','v07-native']:
 selected += [p for p in (root/'work'/name).glob('*') if p.is_file() and p.suffix in ['.py','.c','.h','.txt','.cmd','.patch']]
selected += [p for p in (root/'work/v07-scene').glob('*.py')]
selected += [root/'work/v07-scene/BUILDING.txt',root/'work/v07-scene/PROGRESS.txt']
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(set(selected)):z.write(p,str(p.relative_to(root)).replace('\\','/'))
 z.write(out/'scene-validation.json','VALIDATION.json')
 z.write(root/'work/v07-scene/BUILDING.txt','BUILDING.txt')
# Durable working-source copies without old build trees or game assets.
for name in ['v07-host','v07-portable','v07-bxml','v07-mesh','v07-scripts','v07-native','v07-scene']:
 base=root/'work'/name;dest=root/'src/scene-v07'/name
 for p in selected:
  if p.is_relative_to(base):
   target=dest/p.relative_to(base);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
with zipfile.ZipFile(evidence,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in out.rglob('*'):
  if not p.is_file() or p.suffix not in ['.json','.txt','.log','.png']:continue
  if any(x in ['modules','meshes','fabs','fabs-selected','shell-meshes','shell-fabs'] for x in p.relative_to(out).parts):
   if p.name not in ['module-inventory.json','manifest.json','batch.json']:continue
  z.write(p,str(p.relative_to(out)).replace('\\','/'))
files=[source,evidence,out/'opem-amalur-scene-v0.7-arm64.apk'];report=[{'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
(root/'outputs/v07-package-sha256.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
