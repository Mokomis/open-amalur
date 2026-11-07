from pathlib import Path
import argparse,platform,json,subprocess,sys
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';out=r/'outputs/scene-v08'
p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('category',type=lambda x:int(x,0));p.add_argument('stem');a=p.parse_args()
assert a.name.replace('_','').isalnum() and a.name.isupper();assert a.stem.replace('_','').isalnum() and 1<=a.category<=255
names=[a.stem+'.bin']+[f'{a.stem}_duplicate{i}.bin' for i in range(10)]
for cmd,label in [([sys.executable,str(r/'work/v07-scene/extract_scene_inputs.py'),*names],'extraction'),([sys.executable,str(r/'work/merge_asset_snapshots.py'),'--root',str(r/'work/scene-inputs-v07'),'--glob',f'*/{a.stem}*.bin','--output',str(out/'assets'/(a.stem+'.bin'))],'merge')]:
 q=subprocess.run(cmd,capture_output=True,timeout=240);(out/f'{a.stem}-{label}.txt').write_bytes(q.stdout+q.stderr)
 if q.returncode: print(q.stdout.decode(errors='replace'),q.stderr.decode(errors='replace'));sys.exit(q.returncode)
p=out/'asset-macros.json';j=json.loads(p.read_text());assert not any(m['name']==a.name for m in j);j.append({'name':a.name,'category':a.category,'file':a.stem+'.bin'});p.write_text(json.dumps(j,indent=2));print(json.dumps(j[-1]))
