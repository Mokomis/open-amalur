"""Windows extraction and deterministic variant selection for static scene candidates."""
from pathlib import Path
import platform,subprocess,json,sys,shutil,hashlib
assert platform.system()=='Windows'
root=Path.home()/'Documents/Opem Amalur';out=root/'outputs/scene-v07'
report=json.loads((out/'102-shell-mapping-probe.json').read_text());ids=[str(r['fab_id']) for r in report['fab_parallel_counts']]
assert len(ids)==76 and len(set(ids))==76
names=[i+s for i in ids for s in ['.fab_bxml','.fab_visual_data_streamable_bin']]
r=subprocess.run([sys.executable,str(root/'work/v07-scene/extract_scene_inputs.py'),*names],capture_output=True)
(out/'shell-assets-extraction.log').write_bytes(r.stdout+r.stderr);r.check_returncode()
args=[sys.executable,str(root/'work/v07-mesh/batch_decode_meshes.py'),'--output',str(out/'shell-meshes')]
for a in ['DATA_0.pak','initial_0.pak','patch_0.pak']:args+=['--input-root',str(root/'work/scene-inputs-v07'/a)]
args+=['--ids',*ids]
r=subprocess.run(args,capture_output=True);(out/'shell-meshes-decode.log').write_bytes(r.stdout+r.stderr)
manifest=json.loads((out/'shell-meshes/manifest.json').read_text());selected=root/'work/scene-shell-fabs-selected-v07';selected.mkdir(exist_ok=True)
choices=[]
for rec in manifest['records']:
 if rec['status']!='decoded':continue
 mesh=Path(rec['selected_input']);fab=mesh.with_name(rec['asset_id_text']+'.fab_bxml')
 if not fab.exists():choices.append({'id':rec['asset_id_text'],'status':'missing_same_archive_fab'});continue
 dest=selected/fab.name
 if dest.exists() and dest.read_bytes()!=fab.read_bytes():raise ValueError('stale selected FAB')
 shutil.copy2(fab,dest)
 choices.append({'id':rec['asset_id_text'],'status':'selected_same_archive','fab':str(fab),'sha256':hashlib.sha256(fab.read_bytes()).hexdigest()})
(out/'shell-fab-selection.json').write_text(json.dumps(choices,indent=2))
r=subprocess.run([sys.executable,str(root/'work/v07-mesh/batch_inspect_fabs.py'),'--inputs',str(selected),'--output',str(out/'shell-fabs')],capture_output=True)
(out/'shell-fabs-inspect.log').write_bytes(r.stdout+r.stderr);r.check_returncode()
print(json.dumps({'requested':len(ids),'decoded':manifest['decoded'],'unresolved':manifest['unresolved'],'fab_selected':sum(x['status']=='selected_same_archive' for x in choices)}))
