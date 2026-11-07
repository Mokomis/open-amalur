from pathlib import Path
import hashlib,json,zipfile
r=Path.home()/'Documents/Opem Amalur';p=r/'outputs/opem-amalur-property-decoder-source-20261030.zip'
with zipfile.ZipFile(p,'w',zipfile.ZIP_DEFLATED) as z:
 for f in sorted((r/'work/v13-properties').glob('*')):
  if f.is_file() and f.suffix in ['.py','.js']:z.write(f,'work/v13-properties/'+f.name)
 for name in ['scene_v13_session.py','scene_runtime_cwd.py']:z.write(r/'work'/name,'work/'+name)
 z.write(r/'work/v07-bxml/amalur_blob.py','work/v07-bxml/amalur_blob.py')
 z.write(r/'outputs/scene-v13/PROGRESS.txt','PROGRESS.txt')
manifest=r/'outputs/v13-property-decoder-sha256.json';records=json.loads(manifest.read_text())
for x in records:
 f=r/'outputs'/x['file'];x['bytes']=f.stat().st_size;x['sha256']=hashlib.sha256(f.read_bytes()).hexdigest()
manifest.write_text(json.dumps(records,indent=2));print(json.dumps(records,indent=2))
