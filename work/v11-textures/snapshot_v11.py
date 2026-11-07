from pathlib import Path
import json,hashlib,zipfile,shutil
r=Path.home()/'Documents/Opem Amalur';o=r/'outputs/scene-v11';apk=o/'opem-amalur-scene-v0.11-arm64.apk';m=json.loads((o/'materials-normals.json').read_text());summary=dict(version='0.11.0',status='built-staged-device-not-tested',apk_sha256=hashlib.sha256(apk.read_bytes()).hexdigest(),textured_vertices=m['textured_vertices'],total_vertices=m['vertices'],fallback_vertices=m['fallback_vertices'],texture_count=len(m['textures']),draw_count=m['draws'],gpu_material_bytes=m['gpu_bytes_including_generated_mips'],normals=m['normal_recovery'],collision='Preserved native-corroborated v0.10 static mesh/controller',validation_policy='Batch at milestones; no per-edit rebuild/device test',next='Connect21 source objects and33 type definitions/11 scripts; property-stream reader still pending')
(o/'PROGRESS.txt').write_text('Opem Amalur v0.11 build staged; v0.10 remains installed.\n'+json.dumps(summary,indent=2)+'\n')
(o/'scene-validation.json').write_text(json.dumps(summary,indent=2))
source=r/'outputs/opem-amalur-scene-source-v0.11.zip';evidence=r/'outputs/opem-amalur-scene-evidence-v0.11.zip';selected={}
for folder in ['v11-host','v11-textures','v12-objects']:
 for p in (r/'work'/folder).rglob('*'):
  if not p.is_file() or any(x.startswith('build-') or x in ['__pycache__','simtype-members'] for x in p.relative_to(r/'work'/folder).parts):continue
  if p.suffix not in ['.py','.c','.h','.txt','.xml','.cmd','.cmake','.md'] and p.name!='CMakeLists.txt':continue
  selected[p.relative_to(r).as_posix()]=p
for rel in ['work/v10-scene/texture-profile.json','work/v11-textures/texture-profile.json']:selected[rel]=r/rel
with zipfile.ZipFile(r/'outputs/opem-amalur-scene-source-v0.10.zip') as old,zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
 for info in old.infolist():z.writestr(info,old.read(info.filename))
 for rel,p in selected.items():
  z.write(p,rel);dest=r/'src/scene-v11'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 z.write(o/'PROGRESS.txt','V11_PROGRESS.txt')
with zipfile.ZipFile(evidence,'w',zipfile.ZIP_DEFLATED) as z:
 for p in o.rglob('*'):
  if p.is_file() and p.suffix in ['.json','.txt','.log','.png']:z.write(p,p.relative_to(o).as_posix())
records=[dict(file=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [source,evidence,apk]];(r/'outputs/v11-package-sha256.json').write_text(json.dumps(records,indent=2))
p=r/'outputs/project.json';backup=o/'project-before-scene-v11.json'
if p.exists():
 if not backup.exists():shutil.copy2(p,backup)
 j=json.loads(p.read_text());j['scene_v11_staged']=summary;p.write_text(json.dumps(j,indent=2))
print(json.dumps(records,indent=2))
