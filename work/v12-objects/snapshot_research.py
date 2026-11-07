from pathlib import Path
import json,hashlib,zipfile,shutil
r=Path.home()/'Documents/Opem Amalur';o=r/'outputs/scene-v12'
text='''Opem/Open Amalur checkpoint — 2026-10-30

INSTALLED: v0.10 on OPD2515. Native-corroborated static collision (14,217 triangles) and ~99% architecture texture preview; source/evidence/rollback snapshots preserved.

STAGED: v0.11 APK, not installed/device-tested. Adds all77 prop placements' selected textures and recovered normals;344,346/346,254vertices textured (~99.45%),1,908fallback. No extra runtime test cycle was performed, per the user's batching preference. The existing tablet session was left alone. APK SHA25611c821a2f69749f63765d9fe5fa08b07a5e16ef27529c8f491f00da9acf4e3d8.

OBJECT RESEARCH:21 named source object records located, including exit, alchemyworkbench, containers, crates and activitymarkers. Extracted17 selected type definitions from batch files and resolved33 definitions including ancestors, with11 original Lua scripts identified and no missing ancestors. Parent/script prefix interpretation is corroborated by symbol IDs, but native full property-stream decoding and object-state binding remain unresolved. Nothing here claims object interactions are implemented.

BLOCKER: Accurate native object-property loading is needed before original interaction scripts can be connected. A single bounded Windows startup trace captured only instrumentation readiness, then the original process was no longer present. It captured no selected lookup events; that is inconclusive about the loader. Cause of process exit is unknown, with no matching Application crash event observed. No repeated unchanged runtime launch was attempted.

Tool repair: Frida17.23.2 matches REA6.8's pinned optional dependency. Installed in isolated tools/rea-frida and linked for resolution, using its official prebuilt Windows NAPI binding. REA/client configuration and version were unchanged. A fresh target-free REA worker avoided the old process's cached missing-package result.

CLEANUP/STATE: Frida session closed after detachment; OS verified ownedPID24724 absent and no koa.exe remained. All19 backed-up game-state files retain their original hashes; backup is private under work/v12-objects/native-state-before and is excluded from archives. Original koa.exe file hash is unchanged. Static/native sessions exported and closed. No Astra was used. Credit balance/consumption is not exposed by available tools.

Next focused work: identify the SimType member/property reader or obtain a useful original-game trace, then connect read-only object identity/position/type state before dispatching original callbacks. Workbench's original on_interact calls alchemy_win.open_alchemy_win; the Android alchemy UI/backend is a separate unimplemented layer. Avoid invented successful engine stubs. Continue using Sol, batch builds/tests at meaningful milestones, and preserve v0.10/v0.11 artifacts.
'''
(o/'PROGRESS.txt').write_text(text)
p=o/'object-inventory.json'
if p.exists():
 backup=o/'object-inventory-before-classification.json'
 if not backup.exists():shutil.copy2(p,backup)
 j=json.loads(p.read_text());j['classification']='lighting_candidate_not_actor_records';j['actual_object_inventory']='scene-objects.json';p.write_text(json.dumps(j,indent=2))
summary=dict(status='interaction-property-loader-unresolved',installed_version='0.10.0',staged_version='0.11.0',objects=21,type_definitions_with_ancestors=33,original_scripts=11,native_startup_trace='inconclusive-no-selected-lookup-events',original_state_files_unchanged=19,staged_apk_device_tested=False,rea_version='6.8.0',frida_version='17.23.2',model_policy='Sol only; no Astra without explicit approval',build_policy='Batch at meaningful milestones')
(o/'continuation.json').write_text(json.dumps(summary,indent=2))
source=r/'outputs/opem-amalur-object-research-source-20261030.zip';evidence=r/'outputs/opem-amalur-object-research-evidence-20261030.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((r/'work/v12-objects').glob('*')):
  if p.is_file() and p.suffix in ['.py','.js','.txt']:z.write(p,'work/v12-objects/'+p.name)
 z.write(r/'work/scene_runtime_session.py','work/scene_runtime_session.py');z.write(o/'PROGRESS.txt','PROGRESS.txt')
with zipfile.ZipFile(evidence,'w',zipfile.ZIP_DEFLATED) as z:
 for base,prefix in [(o,'objects'),(r/'outputs/scene-v10/rea-session-live','native-static')]:
  for p in base.rglob('*'):
   if p.is_file() and p.suffix in ['.json','.txt','.log']:z.write(p,prefix+'/'+p.relative_to(base).as_posix())
records=[dict(file=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [source,evidence]];(r/'outputs/v12-research-sha256.json').write_text(json.dumps(records,indent=2))
p=r/'outputs/project.json';backup=o/'project-before-research.json'
if p.exists():
 if not backup.exists():shutil.copy2(p,backup)
 j=json.loads(p.read_text());j['object_research']=summary;p.write_text(json.dumps(j,indent=2))
print(json.dumps(records,indent=2))
