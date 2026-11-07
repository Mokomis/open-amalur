from pathlib import Path
import hashlib,json,shutil,zipfile,platform
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';o=r/'outputs/scene-v17';v16=r/'outputs/scene-v16'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
progress='''Open Amalur v0.13 installed and rendered on OPD2515, 2026-10-30.

Implemented v0.12: engine-owned generational scene handles, original recovered Workbench Lua callback, authored alchemy window service, actual20 reagent/126recipe-reference catalog from isolated patch Lua and exact existing SimType/enum snapshots. Empty project inventory, no imported game save, item grants or DLC entitlement claim. Original callback opened on tablet and user confirmed interaction. Formula crafting remains blocked: native PartFormula source-to-instance ingredient/quantity/product initialization unverified. All126 formula definitions excluded; no fake successful gameplay stub. Host50 interaction checks and35 input checks passed, including original callback, stale handles, transaction fixture and inventory corruption rejection.

Live fixes in v0.13: identified missing actor visual FAB695560 craft_alchemy_table_01 through native Type230417 PartRenderingkind7 field+0x14 (file0x110), native fixup f0cc50. Actual DATA visual parsed completely:8244vertices/2748triangles, two meshes. Added actor reference pose; centralWorkbench now visibly occupies the former empty interaction gap. Native world-matrix arithmetic0xac3a70 tested in standalone x86 probe against79 source prop transforms plusWorkbench transform; no game entrypoint/imports/launch. Direct prior convention disagreed up to214.7756units per100unitbasis, conjugated convention matches within0.00012345. Corrected all77 rendered static placements/140166vertices; old206088 shellvertices remain byte-identical. Desk/bookshelf sourcebones identity; their incorrect world-facing convention is corrected. The object on the wall is a smallbookshelf683980, not another table.

Targeting now ray-tests the actualWorkbench8244vertices, with static collision occlusion, authored300unit reach. It no longer opens from an empty source-origin cone. Source IDs remain separate from engine-owned handle generations and authored pick points. Added explicit renderedWorkbench triangle collision proxy to old14217 native-corroborated static triangles:16965total; addedproxy is NOT native actor physics. Authored spawn uses selected floor without an overhead-collider requirement; real floor/capsule clearance required. v0.12 badspawn behindcage fixed and previousAPKretained. Newspawn[-1412.840576,2049.954834,-315.964478] validatesclearance; actualtablehit286.595units atpitch-.2, occlusion agrees.53collision regression checks pass, along with50interaction/35input checks. Newnative scene354498vertices,58textures,253draws. SignedAPKpayload hashes rechecked; upgrade install-r preservesappdata.

LIMITATIONS: Workbench local inverse static bind is an explicit reference-pose candidate, not native skeletal/bind/animation equivalence. Existing local FAB bind candidates are retained; only scene/world rotation arithmetic is directly confirmed. Workbench material697079 slot0texture697080 fails strict KEEN mip decoder (_3and_0); its surfaces use authored plain fallback. Material696791/texture696826 opaque preview renders; native shaders/glass not reconstructed. Crafting blocked as above, no inventory collection or native save import. Other20scene actors are not spawned/bound. No complete native renderer/gameplay parity claim.

DEVICE: v0.13/code13 packageorg.opemamalur.scene installed on99cc517a, source and originalLua bootstrap completed,354498vertices+58textureGPUupload observed. Screenshot tablet-workbench-visible.png shows centraltable with prompt on surface. User is actively controlling scene; no automated navigation performed. One testtap raced user movement away fromtable and did not produce a newcallback log; do not claim v0.13 onscreenwindow verification from that tap. v0.12 window/callback was actually observed and userconfirmed. Leave controls to user. Previousv0.10/v0.11/v0.12 artifacts preserved. CurrentAPK SHA f42984fc5207e2b60ac84bdb1e88221c65f439fd7c5017e880aedb4710316e8c.

MODEL/PROCESS: Sol only; one scoped SolAlchemy audit worker completed. No Astra, Ghidra coldstart or nativegame launch thispass. Native executable pinnedSHA16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314. Originalcode only loaded as read-only file into standalone pure-arithmetic harness; no filepatch or nativeentrypoint. Exactcredit meter unavailable; nativeformula hunt bounded and stopped at explicit schema gap, builds/tests batched at meaningfulmilestones.

NEXT: Native PartFormula initializer mapping before enabling real crafting; no recipe/output guess. Secondary material697080 requires exact KEEN format/mip evidence; keepfallback until decoded. Validate localWorkbench FAB bind/refpose and animations independently if native parity is needed. Otheractor rendering/scriptservices can reuse newregistry only after recovering correct bindings. Preserve v15 nativecompiledType path; don't restart solvedcompact-format hunt. AllpriorREAsessionsclosed; no newlong-livedsessions.
'''
(o/'PROGRESS.txt').write_text(progress,encoding='utf-8')
(v16/'PROGRESS.txt').write_text('Workbench original Lua callback and authored alchemy catalog interaction shipped in v0.12. Subsequently live furniture/visual issues fixed in v0.13. See outputs/scene-v17/PROGRESS.txt for full continuation.\n',encoding='utf-8')
record=dict(status='installed-rendered-user-controls',version='0.13.0',version_code=13,apk_sha256=sha(o/'opem-amalur-scene-v0.13-arm64.apk'),scene_sha256=json.loads((o/'render-scene.json').read_text())['scene_sha256'],device='99cc517a',original_lua_workbench_callback_tablet_observed_in='0.12.0',v13_tablet_window_recheck='test tap raced user movement; not established',crafting_enabled=False,formula_gap='Native source-to-instance PartFormula initializer missing',reference_pose_bind_native_verified=False,next='Trace exact PartFormula initialization before enabling crafting; decode unsupported table texture separately',credit_meter_available=False)
(o/'continuation.json').write_text(json.dumps(record,indent=2))
state=r/'work/CURRENT_STATE.txt';backup=o/'CURRENT_STATE-before-v17.txt'
if not backup.exists():shutil.copy2(state,backup)
old=state.read_text(encoding='utf-8-sig');marker='V17 WORKBENCH LIVE INTEGRATION'
if marker not in old:state.write_text(old+'\n\n'+marker+' (latest):\n'+json.dumps(record,indent=2)+'\nSee outputs/scene-v17/PROGRESS.txt; source work/v16-host,work/v16-alchemy,work/v17-host,work/v17-props; all older outputs preserved. User active on tablet, leave controls to user.\n',encoding='utf-8')
exe=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe');assert sha(exe)=='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
source=r/'outputs/opem-amalur-scene-source-v0.13.zip';evidence=r/'outputs/opem-amalur-scene-evidence-v0.13.zip'
assert not source.exists()and not evidence.exists()
with zipfile.ZipFile(r/'outputs/opem-amalur-scene-source-v0.11.zip')as previous,zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED)as z:
 for info in previous.infolist():z.writestr(info,previous.read(info.filename))
 for folder in ['v16-host','v16-alchemy','v17-host','v17-props']:
  for p in (r/'work'/folder).rglob('*'):
   if not p.is_file()or any(x.startswith('build-')or x=='__pycache__'for x in p.relative_to(r/'work'/folder).parts):continue
   if p.suffix not in ['.c','.cpp','.h','.py','.txt','.cmd','.cmake','.xml','.inc','.md']and p.name!='CMakeLists.txt':continue
   z.write(p,p.relative_to(r).as_posix())
 z.write(o/'PROGRESS.txt','V17_PROGRESS.txt')
with zipfile.ZipFile(evidence,'w',zipfile.ZIP_DEFLATED)as z:
 for base,prefix in [(v16,'v16'),(o,'v17'),(r/'outputs/scene-v16-alchemy','alchemy')]:
  for p in base.rglob('*'):
   if p.is_file()and p.suffix in ['.json','.txt','.log','.png']:z.write(p,prefix+'/'+p.relative_to(base).as_posix())
files=[source,evidence,o/'opem-amalur-scene-v0.13-arm64.apk'];(o/'package-sha256.json').write_text(json.dumps([dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p))for p in files],indent=2))
p=r/'outputs/project.json';backup=o/'project-before-v17.json'
if p.exists():
 if not backup.exists():shutil.copy2(p,backup)
 j=json.loads(p.read_text());j['scene_v17_live']=record;p.write_text(json.dumps(j,indent=2))
print(json.dumps(record,indent=2));print('source/evidence archives saved; prior files preserved')
