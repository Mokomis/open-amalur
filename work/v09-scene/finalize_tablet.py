from pathlib import Path
import json,shutil
r=Path.home()/'Documents/Opem Amalur';o=r/'outputs/scene-v09'
for name in ['scene-validation.json','PROGRESS.txt','android-apk-manifest.json']:
 p=o/name;backup=o/(name+'.before-tablet')
 if not backup.exists():shutil.copy2(p,backup)
shutil.copy2(o/'opem-amalur-scene-v0.9-validation.json',o/'scene-validation.json');shutil.copy2(r/'work/v09-scene/PROGRESS.txt',o/'PROGRESS.txt')
p=o/'android-apk-manifest.json';v=json.loads(p.read_text());v.update(device_executed=True,device_validation='scene-validation.json');p.write_text(json.dumps(v,indent=2))
for name in ['opem-amalur-scene-source-v0.9.zip','opem-amalur-scene-evidence-v0.9.zip']:
 p=r/'outputs'/name;backup=p.with_name(p.stem+'-before-tablet.zip')
 if not backup.exists():shutil.copy2(p,backup)
p=r/'outputs/project.json'
if p.exists():
 backup=o/'project-before-scene-v09.json'
 if not backup.exists():shutil.copy2(p,backup)
 v=json.loads(p.read_text());v['scene_v09']={'status':'installed-tablet-smoke-passed','apk':'outputs/scene-v09/opem-amalur-scene-v0.9-arm64.apk','validation':'outputs/scene-v09/scene-validation.json','next':'native material/vertex declarations, collision assets and player interaction','rollback':'outputs/scene-v08/opem-amalur-scene-v0.8-arm64.apk'};p.write_text(json.dumps(v,indent=2))
print('Tablet evidence and project continuation state saved.')
