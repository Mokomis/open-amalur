from pathlib import Path
import json,hashlib,zipfile,shutil
r=Path.home()/'Documents/Opem Amalur';o=r/'outputs/scene-v10';apk=o/'opem-amalur-scene-v0.10-arm64.apk'
summary=dict(version='0.10.0',apk_sha256=hashlib.sha256(apk.read_bytes()).hexdigest(),status='installed-and-rendered',architecture_textured_vertices=204180,architecture_vertices=206088,total_vertices=346254,collision_triangles=14217,collision_bvh_bytes=2217916,prior_collision_bvh_bytes=18005272,native_collision_layout_corroborated=True,native_declaration56_corroborated=True,stream_to_declaration_association='matching stride and measured data; selector pending',bootstrap_complete=True,registered_modules=190,tablet='99cc517a OPD2515',tablet_observed=['GPU40textures114draws','recoveredcollisionloaded','Luabootstrapcomplete','movementbetweenfloorsgrounded'],validation_policy='Build and validate at meaningful milestones; no repeated full test suite after each edit.',limitations=['Authored capsule controller; original Bullet filters/dynamics/surface behavior pending.','Opaque slot0 preview, no complete original shader/lighting recovery.','Prop material binding is next; association clue matches172/172 architecture records.'])
(o/'scene-validation.json').write_text(json.dumps(summary,indent=2));p=o/'android-apk-manifest.json';j=json.loads(p.read_text());j['device_executed']=True;j['device_validation']='scene-validation.json';p.write_text(json.dumps(j,indent=2))
progress='''Opem Amalur v0.10 installed. Recovered static collision mesh and native-declared layout56 texture preview integrated.
Architecture texture preview204180/206088vertices (~99%). Collision14,217triangles; BVH2,217,916bytes versusv09 18,005,272bytes. Lua startup complete on tablet,40textureGPU/114draws. User movement betweenfloors observedgrounded in logs.
Do not repeat finished builds/tests: user explicitly prefers batching and forward progress. Use Sol, no Astra without explicit approval. Preserve working v09/v10 rollback files.
Native REA session currentlyopen outputs/scene-v10/rea-session-live; worker uses work/scene-v10-requests. Nextserial026. Nativecollisionproofd70a00/d69880; declarationc658f0.
Next work underway work/v11-textures: prop/material correlation uses FAB descriptor tail0;172/172 architecture matches. Props source JSON outputs/scene-v07/placements.json baked_scene. Preserve exact expanded scene vertex order and transformed position bytes when assigning UVs. Native shader/basecolor semantics remain partlyinferred. Fullgameplay, original player, animation/combat remainunimplemented.
'''
(o/'PROGRESS.txt').write_text(progress)
source=r/'outputs/opem-amalur-scene-source-v0.10.zip';evidence=r/'outputs/opem-amalur-scene-evidence-v0.10.zip';selected={}
for folder in ['v10-host','v10-scene','v10-native']:
 base=r/'work'/folder
 for p in base.rglob('*'):
  if not p.is_file() or any(x.startswith('build-') or x=='__pycache__' for x in p.relative_to(base).parts):continue
  if p.suffix not in ['.py','.c','.h','.txt','.cmake','.xml','.cmd','.md'] and p.name!='CMakeLists.txt':continue
  selected[p.relative_to(r).as_posix()]=p
with zipfile.ZipFile(r/'outputs/opem-amalur-scene-source-v0.9.zip') as old,zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
 for info in old.infolist():z.writestr(info,old.read(info.filename))
 for rel,p in selected.items():
  z.write(p,rel);dest=r/'src/scene-v10'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 z.write(o/'PROGRESS.txt','V10_PROGRESS.txt')
with zipfile.ZipFile(evidence,'w',zipfile.ZIP_DEFLATED) as z:
 for p in o.rglob('*'):
  if p.is_file() and p.suffix in ['.json','.log','.txt','.png']:z.write(p,p.relative_to(o).as_posix())
records=[dict(file=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [source,evidence,apk]];(r/'outputs/v10-package-sha256.json').write_text(json.dumps(records,indent=2))
p=r/'outputs/project.json';backup=o/'project-before-scene-v10.json'
if p.exists():
 if not backup.exists():shutil.copy2(p,backup)
 j=json.loads(p.read_text());j['scene_v10']=summary;p.write_text(json.dumps(j,indent=2))
print(json.dumps(records,indent=2))
