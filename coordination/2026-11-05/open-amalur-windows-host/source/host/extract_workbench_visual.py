"""Windows read-only extraction of exact Workbench visual dependencies to a new scope."""
from pathlib import Path
import hashlib,json,subprocess,platform
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';g=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning');o=r/'outputs/scene-v17';o.mkdir(exist_ok=True)
names=['695560.fab_bxml','695560.fab_visual_data_streamable_bin'];rows=[]
for archive,listing in [('DATA_0.pak','DATA-archive-list.txt'),('initial_0.pak','initial-archive-list.txt'),('patch_0.pak','patch-archive-list.txt')]:
 b=(r/'outputs'/listing).read_bytes();text=b.decode('utf-16'if b.startswith(b'\xff\xfe')else'utf-8-sig');inventory={x.strip()for x in text.splitlines()};selected=[n for n in names if n in inventory]
 if not selected:continue
 dest=r/'work/v17-inputs'/archive;dest.mkdir(parents=True,exist_ok=True);missing=[n for n in selected if not(dest/n).exists()]
 if missing:
  run=subprocess.run([str(g/'modding/pakfileunpacker.exe'),str(g/'data'/archive),'unpack',str(dest),*missing],cwd=g/'modding',capture_output=True,timeout=120);(o/(archive+'-extract.log')).write_bytes(run.stdout+run.stderr);assert not run.returncode
 for n in selected:
  p=dest/n;b=p.read_bytes();rows.append(dict(archive=archive,file=n,path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
(o/'workbench-visual-inputs.json').write_text(json.dumps(dict(native_reference=dict(type_id=230417,component_kind=7,record_file_offset=252,key_field_offset=0x14,key_file_offset=0x110,fab_id=695560,native_fixup_function='0xf0cc50'),variants=rows,selection='initial_0.pak explicit preview asset; native mount precedence not inferred'),indent=2))
print(json.dumps(rows))
