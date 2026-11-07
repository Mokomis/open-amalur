from pathlib import Path
import argparse,json,hashlib,subprocess,csv,shutil
w=Path(__file__).resolve().parent;r=w.parents[1];base=r/'work/v40-windows-host/assets/world'
p=argparse.ArgumentParser();p.add_argument('action',choices=['apply','restore']);a=p.parse_args()
rows=csv.reader(subprocess.check_output(['tasklist','/FI','IMAGENAME eq open-amalur-windows.exe','/FO','CSV','/NH'],text=True).splitlines())
if any(row and row[0].lower()=='open-amalur-windows.exe'for row in rows):raise SystemExit('Close the custom preview before changing its asset pack')
m=json.loads((w/'visual-collision-manifest.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()if p.exists()else None
backup=w/'before-visual-collision';backup.mkdir(exist_ok=True)
# Validate the complete transaction before writing any file.
for name,v in m['files'].items():
 assert Path(name).name==name
 current=sha(base/name)
 if a.action=='apply':
  assert current in [v['before_sha256'],v['sha256']],('Live pack drift',name)
  if v['before_sha256']is not None and current==v['sha256']:
   assert sha(backup/name)==v['before_sha256'],('Missing original backup',name)
  assert sha(w/'visual-collision-overlay'/name)==v['sha256']
 else:
  assert current==v['sha256'],('Live overlay drift',name)
  if v['before_sha256']is not None:assert sha(backup/name)==v['before_sha256']
for name,v in m['files'].items():
 dst=base/name
 if a.action=='apply':
  if v['before_sha256']is not None and not(backup/name).exists():shutil.copy2(dst,backup/name)
  data=(w/'visual-collision-overlay'/name).read_bytes()
 else:
  if v['before_sha256']is None:dst.unlink();continue
  data=(backup/name).read_bytes()
 tmp=dst.with_suffix('.oa-v42-tmp');tmp.write_bytes(data);tmp.replace(dst)
(w/'visual-collision-deployment.json').write_text(json.dumps({'action':a.action,'files':len(m['files']),'scope':'Windows desktop assets only'},indent=2));print(a.action,len(m['files']),'files')
