"""Preserve the bounded investigation; no further native queries or decoder edits."""
from pathlib import Path
import hashlib,json,shutil,zipfile
r=Path.home()/'Documents/Opem Amalur';a=r/'outputs/scene-v14-astra';o=r/'outputs/scene-v14-sol'
state=json.loads((a/'continuation.json').read_text());assert state['status']=='target-not-achieved' and state['decoded_real_compact_types']==0
assert json.loads((a/'rea-session-live/status.json').read_text())['state']=='closed'
integrity=json.loads((a/'rea-session-live/input-integrity.json').read_text());assert integrity['unchanged'] and integrity['sha256_after']=='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
fixtures=json.loads((o/'real-inputs-manifest.json').read_text());assert len(fixtures['inputs'])==33
for row in fixtures['inputs']:
 raw=Path(row['file']).read_bytes();assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
summary=dict(status='focused-astra-attempt-ended; compact-native-decoder-unresolved',investigation_model='gpt-6-astra',reasoning_effort='high',astra_workers=1,implementation_handoff='Returned to Sol workflow; no native-confirmed compact implementation justified',decoded_real_compact_types=0,real_inputs_preserved=33,submitted_decompiler_requests=20,invalid_schema_requests=4,matching_function_records=15,detected_address_fallbacks=1,rejected_followups_not_executed=state['rejected_followups_not_executed'],approval_rejection_reason='Additional native queries exceeded the roughly20-query bound set by the parent for the focused attempt',native_session_closed=True,executable_unchanged=True,game_launched=False,android_builds_or_changes=False,exact_credit_meter_available=False,installed_version_preserved='0.10.0',staged_version_preserved='0.11.0',findings='../scene-v14-astra/FINDINGS.txt')
(o/'handoff.json').write_text(json.dumps(summary,indent=2))
text='''Open Amalur — Astra High focused decoder attempt, 2026-10-30 local

The focused Astra High worker completed, but the requested milestone was NOT achieved: zero real compact SimTypes decoded with native field evidence. One real target was preserved exactly (Workbench230417,33bytes,SHA502a854c3f09c5226468542c3c0d0ea2c85bd28b0435bd93c3dd99523e024207); all33 selected/ancestor inputs are preserved with provenance hashes. No compact decoder implementation is justified; interaction dispatch remains disabled. The existing Sol workflow retains the handoff. There is no further Astra work running.

Useful findings: ordinary stream decompression, catalog initialization, the examined newer resource-factory wrappers, and alternate callback do not reveal the conversion. These are bounded static findings, not proof that all related paths lack one. The record tails contain plausible component lists, but those observations are not a native-confirmed schema. TypeMgr185 remains unproven as an extension or schema identifier.

Investigation accounting:20 submitted decompiler requests included4 schema errors and16 returned records;15 matched their requested function and1 address fallback was detected/excluded. Detailed native addresses, evidence IDs and limitations are in outputs/scene-v14-astra/FINDINGS.txt and evidence-index.json. Exact app credit consumption is unavailable.

Automatic approval review rejected two further native queries (0xa8cd70 and0xb030a0), stating that they exceeded the roughly20-query bound I set for this focused attempt. They did not execute and were not retried by another route. These are unexamined next call edges, not established decoders.

All evidence was exported, the REA session closed, and the original executable hash remained unchanged. No game launch, new build, Android install, runtime feature change, or tablet action occurred. Installedv0.10, stagedv0.11 and earlier progress remain preserved. No build/test cycle was warranted because no decoder or engine implementation changed; only provenance and evidence-integrity checks were performed.

Next decisive evidence: a native reader consuming the actual compact source bytes, or a working interactive Windows capture linking those bytes to the compiled Type consumer. The previous SSH/session0 startup trace should not be repeated unchanged. A further static continuation would require revisiting the scope that automatic approval review rejected. This handoff does not claim that switching model alone resolved the format.
'''
(o/'HANDOFF.txt').write_text(text);(r/'outputs/opem-amalur-astra-decoder-attempt-20261030.txt').write_text(text)
checkpoint='''\nV14 ASTRA HIGH FOCUSED ATTEMPT (latest):
User authorizedONE AstraHigh investigation thenSol implementation, batchbuilds/tests. One gpt-6-astra/high worker finished; native compact decoder targetNOTachieved,0realtypesdecoded. Findings outputs/scene-v14-astra/FINDINGS.txt, continuation.json,evidence-index.json. All33realinputfixtures work/v14-sol/real-inputs (8829bytes) provenanceverified; manifestoutputs/scene-v14-sol/real-inputs-manifest.json. Nativeeliminations bounded: zlib-styleStreamable b017b0/b01820;Segmentedb01630;managercataloga732d0;examinedkeenBlob/Fallbackfactorymethods;actualalternatecallbacka6f990 viaRAW(notfallbacke70560);resourcewrapperb03160->a8cd70anda90140->b030a0. No nativecompactfieldcontract. TypeMgr185meaningunproven;0x94is.bigentryflag,notextensionenum.20decompilerrequests=4schemaerrors+16records(15functionmatches,1detectedfallback). AutomaticapprovalreviewREJECTEDfollowupa8cd70/b030a0 forexceedingparentroughly20querybound;NOTEXECUTED,noalternate-route retry. DoNOTsilentlyretryrejectedactions. Session work/scene_v14_astra_session.py requestswork/scene-v14-astra-requests/shutdown exists; outputs/scene-v14-astra/rea-session-live CLOSED/exported/snapshot/hashunchanged. No nativegame/apps/builds/tests/tabletchanges. No compact implementationjustified;dispatcherdisabled. Solhandoffoutputs/scene-v14-sol/HANDOFF.txt/handoff.json, authoredhelperwork/v14-sol. Source/evidenceZIPs+SHA manifestoutputs/. Exactcreditmeterunavailable. Existingv10installed/v11stagedpreserved. Nextrequiresnewdecisivecompactreader/interactivetraceevidence; no repeatedunchangedSSHstartup.\n'''
with (r/'work/CURRENT_STATE.txt').open('a') as f:f.write(checkpoint)
project=r/'outputs/project.json'
if project.exists():
 backup=o/'project-before-v14.json'
 if not backup.exists():shutil.copy2(project,backup)
 doc=json.loads(project.read_text());doc['native_property_astra_attempt']=summary;project.write_text(json.dumps(doc,indent=2))
source=r/'outputs/opem-amalur-astra-decoder-source-20261030.zip';evidence=r/'outputs/opem-amalur-astra-decoder-evidence-20261030.zip'
with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
 for directory in ['v14-sol','v14-astra']:
  for p in sorted((r/'work'/directory).glob('*.py')):z.write(p,'work/'+directory+'/'+p.name)
 z.write(r/'work/scene_v14_astra_session.py','work/scene_v14_astra_session.py')
 z.write(o/'HANDOFF.txt','HANDOFF.txt')
with zipfile.ZipFile(evidence,'w',zipfile.ZIP_DEFLATED) as z:
 for directory in [a,o]:
  for p in sorted(directory.rglob('*')):
   if not p.is_file() or 'prior-evidence' in p.parts or p.name=='analysis.snapshot.json':continue
   if p.suffix in ['.json','.txt','.log']:z.write(p,directory.name+'/'+p.relative_to(directory).as_posix())
 for p in sorted((r/'outputs/bytecode-reader').glob('v14-*.json')):z.write(p,'native-disassembly/'+p.name)
manifest=[dict(file=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in [source,evidence]]
(r/'outputs/v14-astra-decoder-sha256.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))
