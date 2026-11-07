from pathlib import Path
import hashlib,json,zipfile,shutil
r=Path.home()/'Documents/Opem Amalur';o=r/'outputs/scene-v13'
static=json.loads((o/'rea-session-live/status.json').read_text());runtime=json.loads((o/'rea-runtime-cwd/status.json').read_text());assert static['state']==runtime['state']=='closed'
for directory in ['rea-session-live','rea-runtime-cwd']:
 assert json.loads((o/directory/'input-integrity.json').read_text())['unchanged']
status=json.loads((o/'rea-runtime-cwd/trace_status.json').read_text())['structuredContent']['normalized_result'];owned=json.loads((o/'rea-runtime-cwd/owned-process.json').read_text());assert status['pid']==owned['pid']==39684
import subprocess
check=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',f"$p=Get-Process -Id {owned['pid']} -ErrorAction SilentlyContinue; if($p){{exit 1}}; if(Get-Process koa -ErrorAction SilentlyContinue){{exit 2}}"],capture_output=True)
if check.returncode:raise RuntimeError('Game process disposition requires review')
backup=json.loads((r/'work/v13-properties/native-state-before-cwd/manifest.json').read_text());unchanged=0
for row in backup['files']:
 if hashlib.sha256(Path(row['source']).read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Game state changed')
 unchanged+=1
components=json.loads((o/'component-map.json').read_text());assert len(components['components'])==43 and all(x['native_kind_getter_verified'] for x in components['components'])
summary=dict(status='blocked-on-compact-SimType-conversion',native_component_kinds=43,native_kind_getters_verified=43,scene_objects=21,candidate_type_nodes=33,recovered_scripts_linked_as_candidates=11,enabled_interactions=0,decoder='guarded prototype for native compiled Type carrier; no real compiled Type input validated',validation='5 synthetic contract/bounds cases passed; all 33 provenance-verified real compact members correctly refused',native_runtime=dict(exit_code=1,selected_type_or_reader_events=0,owned_pid=owned['pid'],process_absent=True,frida_session_closed=True,launch_cwd='original game directory',limitation='SSH launch occurs in Windows session 0; no Steam client was observed. Interactive startup cause unconfirmed.'),state_files_unchanged=unchanged,original_executable_unchanged=True,static_session_closed=True,tablet_changes=False,android_build_or_install=False,installed_version='0.10.0',staged_version='0.11.0',model_escalation=False,credit_meter_available=False)
(o/'continuation.json').write_text(json.dumps(summary,indent=2))
text='''Open Amalur native property research — 2026-10-30

Result: confirmed all43 native component kinds from allocator vtables/RTTI and independent kind getters. Relevant kinds:22 CustomInteraction,33 Lockable,34 Interaction,35 Script. The compiled Type reader0x1001070 resolves parent+0x20, Lua script+0x10, dependencies pointer+0x14/count+0x18, component base+0x24/count+0x28/offsets+0x2c. Factory0xfa3d20 dispatches kinds0..42. Interaction resolver0xf0c960 walks references at component+4/count+8; CustomInteraction0xf0d3b0 converts key+4. Reference roles and other fields remain opaque. Native evidence is static, from original koa.exe SHA16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314.

Implementation: work/v13-properties/compiled_type.py provides a bounded, non-mutating prototype for that compiled carrier. It preserves original key words, validates relocation slots and payload bounds, and refuses the distinct compact SimType stream. It does not pretend to decode source member properties. Five synthetic contract/bounds tests passed in one Windows batch; every truncation of the fixture and nine pointer/count/kind corruptions were rejected. All33 actual selected/ancestor compact inputs were provenance/hash verified and correctly refused. No successful real compiled Type fixture or native runtime parity is claimed.

Data links: interaction-manifest.json connects21 source scene objects to33 candidate ancestry definitions and11 recovered Lua scripts. All dispatches remain disabled. Callback keys/global names are literal source observations, not a complete call graph. Native instance-state binding and gameplay/UI services remain unimplemented. Workbench's original interaction opens alchemy_win; that Android UI/backend still needs a real implementation.

Additional observations: simtype_mgr.bundle and duplicate0 are23-byte dependency lists, not the missing schema. Partset8129 and8119 are valid relocation carriers with uint arrays[6] and[6,7,10], matching native Location/Rendering/Item kinds; this component-list interpretation remains an inference until its native consumer is traced. Compact standalone SimTypes share the compact batch-member shape. Do not assume the compiled reader accepts either. Candidate parent/script prefix interpretation from v12 is still not native-confirmed.

Changed runtime trace: launched the original game with its own folder as CWD and hooked exit functions plus selected type/reader entries, bounded45seconds/64events. Captured explicit ExitProcess(1), with no selected type/reader events. Runtime addresses/backtrace retained in rea-runtime-cwd/trace_status.json. This rules out the earlier unexplained disappearance but does not identify the startup cause. The SSH process is in Windows session0 and no Steam client was observed; interactive-launch failure is a hypothesis, not proof. No further launch or repeated unchanged trace was performed. OwnedPID39684 is absent; Frida detached/closed. All19 backed-up state files and original executable hashes are unchanged. Both REA sessions exported and closed; private state backups are excluded from deliverables.

Research caution: REA procedure_pseudo_code('0xa6e140') resolved to unrelated FUN_00e6ecf0 because the intended callback lacked a recognized function boundary. Ignore asset_request_callback.json as evidence about0xa6e140; raw v13-bundle-callback.json disassembly supplies the actual callback. Type virtual+8 is teardown, not a serialized reader. Blueprint vtables have four confirmed slots; do not interpret adjacent slot+0x10 data as another virtual method.

Blocker and next step: recover the compact SimType-to-compiled conversion through the native batch/property path, or obtain a working native-game capture from an interactive Windows desktop. Current static Type reader and generic request getters have not supplied that conversion. More repetitions of the same startup trace would add little evidence. This is a difficult reverse-engineering boundary; no Astra/model escalation was used. No live credit meter is exposed, so exact credit consumption cannot be reported.

Device/build state: installedv0.10 and stagedv0.11 are preserved. No new Android build, installation, gameplay input, or tablet session change. Continue Sol only and batch builds/tests at meaningful milestones. Existing source/assets/build artifacts remain intact.
'''
(o/'PROGRESS.txt').write_text(text)
(r/'outputs/opem-amalur-properties-progress-20261030.txt').write_text(text)
checkpoint='''\nV13 NATIVE PROPERTY CHECKPOINT (latest; supersedes v12 blocker description):
See outputs/scene-v13/PROGRESS.txt and continuation.json. All43 component kinds mapped with native RTTI + kind-getter confirmation. compiled_type.py reads ONLY native compiled carriers; compact source conversion is UNRESOLVED. Windows batch:5 synthetic tests pass; all33 real compact members hash-verified and refused. interaction-manifest21objects/33candidateTypes/11scripts, dispatchdisabled. Type reader1001070 parent20/script10/deps14,18/componentbase24,count28,offsets2c (hex). Parts22custominteraction,33lockable,34interaction,35script. Root4-byte keys retained before a70b80 native conversion; reference semantic roles not inferred. No real compiledType fixture validated. Partset8129/8119 observed arrays[6]/[6,7,10]; component-list role inferred only. simtype_mgr.bundle23bytes dependencylist, notschema. StaticGhidra and fresh runtime worker BOTH CLOSED, input integrity unchanged. Changed startup trace game-folderCWD capturedExitProcess1 beforetypes; PID39684absent,19statefilesunchanged; evidence outputs/scene-v13/rea-runtime-cwd. SSHsession0/noSteamobserved, interactive-startup causeUNCONFIRMED. No further repeatedtrace. Nativequeriesv13-bundle-callback rawdisassemblyvalid; asset_request_callback.json isWRONGADDRESS fallbacke6ecf0, ignoreasproofa6e140. No Androidbuild/install; installedv10/stagedv11preserved. Workstoppedatdifficultcompactconversionboundary, notsuccessfulinteractions. All authoredhelperswork/v13-properties; source/evidenceZIPsoutputs/. No memoryupdate or modelescalation. Exactcreditmeterunavailable. Nexttrace needschangedinteractiveWindowslaunch/evidence; don'tredo completedbuilds/tests or Ghidracoldstartwithoutfocusedneed.\n'''
with (r/'work/CURRENT_STATE.txt').open('a') as f:f.write(checkpoint)
project=r/'outputs/project.json'
if project.exists():
 shutil.copy2(project,o/'project-before-v13.json');j=json.loads(project.read_text());j['native_property_research']=summary;project.write_text(json.dumps(j,indent=2))
source=r/'outputs/opem-amalur-property-decoder-source-20261030.zip';evidence=r/'outputs/opem-amalur-property-decoder-evidence-20261030.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted((r/'work/v13-properties').glob('*')):
  if p.is_file() and p.suffix in ['.py','.js']:z.write(p,'work/v13-properties/'+p.name)
 for name in ['scene_v13_session.py','scene_runtime_cwd.py']:z.write(r/'work'/name,'work/'+name)
 z.write(r/'work/v07-bxml/amalur_blob.py','work/v07-bxml/amalur_blob.py')
 z.write(o/'PROGRESS.txt','PROGRESS.txt')
with zipfile.ZipFile(evidence,'w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(o.rglob('*')):
  if p.is_file() and p.suffix in ['.json','.txt','.log'] and p.name!='analysis.snapshot.json':z.write(p,p.relative_to(o))
 for p in sorted((r/'outputs/bytecode-reader').glob('v13-*.json')):z.write(p,'native-disassembly/'+p.name)
records=[dict(file=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [source,evidence]]
(r/'outputs/v13-property-decoder-sha256.json').write_text(json.dumps(records,indent=2));print(json.dumps(dict(state_files_unchanged=unchanged,deliverables=records),indent=2))
