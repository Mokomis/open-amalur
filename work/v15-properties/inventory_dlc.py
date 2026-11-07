from pathlib import Path
import subprocess,json,collections,hashlib
r=Path.home()/'Documents/Opem Amalur';g=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning');pak=g/'data_1278260/dlc_mit_0.pak';out=r/'outputs/scene-v15';p=out/'dlc-archive-list.txt'
if not p.exists():
 run=subprocess.run([str(g/'modding/pakfileunpacker.exe'),str(pak),'list'],cwd=g/'modding',capture_output=True,timeout=180)
 (out/'dlc-list-stderr.txt').write_bytes(run.stderr)
 if run.returncode:raise ValueError(f'Listing failed: {run.returncode}')
 p.write_bytes(run.stdout)
b=p.read_bytes();text=b.decode('utf-16' if b.startswith(b'\xff\xfe') else 'utf-8-sig');lines=[x.strip() for x in text.splitlines()];names=[x for x in lines if x and '.' in x and ' ' not in x];counts=collections.Counter(x.split('.',1)[-1] for x in names)
selected=[x for x in names if x.endswith('.simtype_bxml')];report=dict(archive=str(pak),archive_bytes=pak.stat().st_size,list_sha256=hashlib.sha256(b).hexdigest(),names=len(names),type_files=selected,related_extensions={k:v for k,v in counts.items() if any(z in k for z in ['simtype','partset','bundle'])},first_lines=lines[:10])
(out/'dlc-inventory.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
