"""Windows-only bounded extraction. Variants preserved; no mount precedence claim."""
from pathlib import Path
import hashlib,json,platform,subprocess,sys
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';g=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning');o=r/'outputs/scene-v18';rows=[];names=sys.argv[1:]
assert names and len(names)<=200 and all(Path(n).name==n and '/'not in n and '\\'not in n for n in names)
manifest=o/'lighting-asset-inputs.json'
if manifest.exists():rows=json.loads(manifest.read_text())
for archive,label in [('DATA_0.pak','DATA'),('initial_0.pak','initial'),('patch_0.pak','patch')]:
 b=(r/f'outputs/{label}-archive-list.txt').read_bytes();inventory=set(x.strip()for x in b.decode('utf-16'if b.startswith(b'\xff\xfe')else'utf-8-sig').splitlines());selected=[n for n in names if n in inventory]
 if not selected:continue
 dest=r/'work/v18-inputs'/archive;dest.mkdir(parents=True,exist_ok=True);missing=[n for n in selected if not(dest/n).exists()]
 if missing:
  result=subprocess.run([str(g/'modding/pakfileunpacker.exe'),str(g/'data'/archive),'unpack',str(dest),*missing],cwd=g/'modding',capture_output=True,timeout=120);(o/(archive+'-'+hashlib.sha256('\n'.join(missing).encode()).hexdigest()[:8]+'.log')).write_bytes(result.stdout+result.stderr);assert not result.returncode
 for n in selected:
  p=dest/n;b=p.read_bytes();row=dict(archive=archive,file=n,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),first64_hex=b[:64].hex());rows=[x for x in rows if(x['archive'],x['file'])!=(archive,n)]+[row]
manifest.write_text(json.dumps(rows,indent=2));print(json.dumps([x for x in rows if x['file']in names]))
