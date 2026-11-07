"""Extract caller-selected existing asset names into isolated per-archive copies."""
import argparse,hashlib,json,platform,subprocess
from pathlib import Path
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur'
game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning')
ap=argparse.ArgumentParser();ap.add_argument('names',nargs='+');args=ap.parse_args()
assert all(Path(n).name==n and '/' not in n and '\\' not in n for n in args.names)
out=root/'outputs/scene-v09';out.mkdir(parents=True,exist_ok=True)
records=[]
for archive,listing in [('initial_0.pak','initial-archive-list.txt'),('DATA_0.pak','DATA-archive-list.txt'),('patch_0.pak','patch-archive-list.txt')]:
    data=(root/'outputs'/listing).read_bytes();text=data.decode('utf-16' if data.startswith(b'\xff\xfe') else 'utf-8-sig')
    inventory={s.strip() for s in text.splitlines()};selected=[n for n in args.names if n in inventory]
    if not selected:continue
    dest=root/'work/scene-inputs-v09'/archive;dest.mkdir(parents=True,exist_ok=True)
    missing=[n for n in selected if not (dest/n).exists()]
    if missing:
        run=subprocess.run([str(game/'modding/pakfileunpacker.exe'),str(game/'data'/archive),'unpack',str(dest),*missing],
                           cwd=game/'modding',capture_output=True,timeout=120)
        label=hashlib.sha256('\n'.join(missing).encode()).hexdigest()[:12]
        (out/f'extract-{archive}-{label}.log').write_bytes(run.stdout+run.stderr)
        if run.returncode:raise RuntimeError(f'unpacker {archive}: exit {run.returncode}')
    for name in selected:
        p=dest/name;raw=p.read_bytes()
        records.append({'archive':archive,'file':name,'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
                        'first64_hex':raw[:64].hex()})
manifest=out/'extracted-inputs.json'
old=json.loads(manifest.read_text())['records'] if manifest.exists() else []
merged={(r['archive'],r['file']):r for r in old+records}
manifest.write_text(json.dumps({'scope':'Three inventoried archives; variants remain separate, native mount precedence not assumed.','records':list(merged.values())},indent=2),encoding='utf-8')
print(json.dumps(records,indent=2))
