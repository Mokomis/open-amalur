from pathlib import Path
import shutil,json,hashlib
r=Path.home()/'Documents/Opem Amalur';dest=r/'work/v15-properties/native-state-before-interactive';dest.mkdir(exist_ok=False);home=Path.home();sources=[]
for base in [home/'Documents/My Games',home/'Saved Games']:
 if base.exists():sources.extend(p for p in base.iterdir() if p.is_dir() and any(s in p.name.lower() for s in ['reckoning','amalur']))
steam=Path(r'C:\Program Files (x86)\Steam\userdata')
if steam.exists():sources.extend(p/'1041720' for p in steam.iterdir() if p.is_dir() and (p/'1041720').exists())
records=[];total=0
for i,source in enumerate(sources):
 files=[p for p in source.rglob('*') if p.is_file() and not p.is_symlink()];total+=sum(p.stat().st_size for p in files)
 if total>512*1024*1024:raise ValueError('State backup exceeds bounded copy; do not run target')
 for p in files:
  rel=p.relative_to(source);target=dest/str(i)/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target);records.append(dict(source=str(p),backup=str(target),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
(dest/'manifest.json').write_text(json.dumps(dict(files=records,total_bytes=total),indent=2));print(json.dumps(dict(backup_roots=len(sources),files=len(records),bytes=total)))
