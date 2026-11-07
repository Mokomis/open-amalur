"""Complete cross-archive selection only when every extracted candidate is identical."""
from pathlib import Path
import platform,hashlib,json,subprocess,sys,shutil
assert platform.system()=='Windows'
root=Path.home()/'Documents/Opem Amalur';out=root/'outputs/scene-v07';p=out/'shell-fab-selection.json';rows=json.loads(p.read_text())
for row in rows:
 if row['status']!='missing_same_archive_fab':continue
 candidates=list((root/'work/scene-inputs-v07').glob('*/'+row['id']+'.fab_bxml'))
 hashes={hashlib.sha256(q.read_bytes()).hexdigest() for q in candidates}
 if len(hashes)!=1:row['reason']='Cross-archive candidates absent or conflicting';continue
 q=candidates[0];shutil.copy2(q,root/'work/scene-shell-fabs-selected-v07'/q.name)
 row.update(status='selected_unique_cross_archive',fab=str(q),sha256=next(iter(hashes)),all_candidates=[str(x) for x in candidates])
p.write_text(json.dumps(rows,indent=2))
r=subprocess.run([sys.executable,str(root/'work/v07-mesh/batch_inspect_fabs.py'),'--inputs',str(root/'work/scene-shell-fabs-selected-v07'),'--output',str(out/'shell-fabs')],capture_output=True)
(out/'shell-fabs-inspect.log').write_bytes(r.stdout+r.stderr);r.check_returncode();print('selected',sum(r['status'].startswith('selected_') for r in rows),'of',len(rows))
