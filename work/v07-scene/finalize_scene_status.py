"""Persist the verified v0.7 state, preserving earlier milestone metadata."""
from pathlib import Path
import platform,json,shutil,hashlib
assert platform.system()=='Windows'
root=Path.home()/'Documents/Opem Amalur';out=root/'outputs/scene-v07'
validation=json.loads((out/'scene-validation.json').read_text());tablet=json.loads((out/'tablet-validation.json').read_text());apk=json.loads((out/'android-apk-manifest.json').read_text())
assert apk['sha256']==tablet['apk_sha256']==validation['android']['apk_sha256']
assert hashlib.sha256(Path(apk['apk']).read_bytes()).hexdigest()==apk['sha256']
apk.update(device_executed=True,device_rendering_verified=True,device_model='OPD2515',device_validation='tablet-validation.json',orbit_drag_verified=True)
(out/'android-apk-manifest.json').write_text(json.dumps(apk,indent=2)+'\n')
p=root/'outputs/project.json';backup=root/'outputs/project-before-v07.json'
if not backup.exists():shutil.copy2(p,backup)
j=json.loads(p.read_text());j['scene_v07']={'status':'Windows-built Android scene viewer installed and visibly rendered on attached OPD2515',
 'scene_id':524859,'primary_static_assemblies':172,'prop_instances':77,'triangles':115418,'android_apk_sha256':apk['sha256'],
 'source_directory':str(root/'src/scene-v07'),'validation':str(out/'scene-validation.json'),'report':str(out/'PROGRESS.txt'),
 'script_status':'178modules register; real initialization stops at INPUT.is_east_asian_controller_button_swap_required. Root/event incomplete.',
 'next_work':['Implement or model native controller/platform state for INPUT service, with explicit Android behavior.','Verify prop transform arithmetic against native consumer; preserve current inferred status.','Recover secondary render sets and materials/textures.','Add persistent script realm, player input, collision and animation toward playable slice.']}
p.write_text(json.dumps(j,indent=2)+'\n')
shutil.copy2(root/'work/v07-scene/PROGRESS.txt',out/'PROGRESS.txt');shutil.copy2(root/'work/v07-scene/BUILDING.txt',out/'BUILDING.txt')
print('v0.7 status saved; matching installed APK and unchanged original executable evidence preserved')
