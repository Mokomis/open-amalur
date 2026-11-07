"""Windows-only private source/evidence snapshot; excludes extracted game data."""
from pathlib import Path
import platform,json,hashlib,zipfile,shutil
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';out=r/'outputs/scene-v08';selected=[]
for name in ['v08-host','v08-portable','v08-native','v08-scripts','v08-scene']:
 base=r/'work'/name
 for p in base.rglob('*'):
  if not p.is_file() or any(x.startswith('build-') or x=='__pycache__' for x in p.relative_to(base).parts):continue
  if p.suffix.lower() not in ['.c','.h','.lua','.py','.txt','.cmake','.xml','.cmd','.ps1','.patch','.md'] and p.name not in ['CMakeLists.txt','COPYRIGHT','LICENSE','README','Makefile']:continue
  if p.name.endswith('-original.lua') or p.name.endswith('-current.c') or p.name.endswith('-current.txt') or p.name in ['vm_a_pseudocode.c']:continue
  selected.append(p)
for name in ['merge_asset_snapshots.py','probe_snapshot_names.py','prepare_macro.py','run_bootstrap.py','test_inspector_macros.py','run_windows_validation.py','adapt_scene_modules.py']:
 p=r/'work'/name
 if p.exists():selected.append(p)
selected.append(out/'asset-macros.json')
for name in ['amalur_bxml.py','amalur_enums.py','amalur_native_enums.py','test_amalur_enums.py','108_probe_compiled_enums.py']:
 selected.append(r/'work/v07-bxml'/name)
for relative in ['work/v07-scripts/export_scene_modules.py','work/v07-scripts/module_source_adapter.py','work/v07-scene/extract_scene_inputs.py','work/v06-compare/native_vm_harness.c']:
 selected.append(r/relative)
# Keep the authored instructions canonical; avoid shipping an old output copy.
shutil.copy2(r/'work/v08-scene/BUILDING.txt',out/'BUILDING.txt')
for p in selected:
 if not p.is_file():raise FileNotFoundError('Required source/helper missing: '+str(p))
source=r/'outputs/opem-amalur-scene-source-v0.8.zip';evidence=r/'outputs/opem-amalur-scene-evidence-v0.8.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in sorted(set(selected)):
  rel=p.relative_to(r);z.write(p,rel.as_posix());dest=r/'src/scene-v08'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 for name in ['PROGRESS.txt','BUILDING.txt','scene-validation.json']:z.write(out/name,name)
with zipfile.ZipFile(evidence,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
 for p in out.rglob('*'):
  if not p.is_file() or p.suffix.lower() not in ['.json','.txt','.log','.png']:continue
  rel=p.relative_to(out)
  if 'modules' in rel.parts and p.name not in ['module-inventory.json','handle-key-adaptation.json','runtime-adaptation.json']:continue
  if 'inspector-macro-tests' in rel.parts and p.name!='results.json':continue
  z.write(p,rel.as_posix())
records=[]
for p in [source,evidence,out/'opem-amalur-scene-v0.8-arm64.apk']:
 records.append({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(r/'outputs/v08-package-sha256.json').write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
