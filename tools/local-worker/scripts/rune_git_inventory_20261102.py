from pathlib import Path
import hashlib,json,subprocess,tarfile,time
root=Path(r'C:\OpenRune\work\SurrealEngine');out=Path(r'C:\OpenRune\outputs\github-sync-20261102');out.mkdir(parents=True,exist_ok=True)
def git(*args):return subprocess.check_output(['git','-C',str(root),*args])
head=git('rev-parse','HEAD').decode().strip()
changed=set(git('diff','--name-only','HEAD','-z').decode().strip('\0').split('\0'))|set(git('ls-files','--others','--exclude-standard','-z').decode().strip('\0').split('\0'));changed.discard('')
mode={}
for r in git('ls-files','--stage','-z').decode().split('\0'):
 if r:
  meta,name=r.split('\t',1);mode[name]=meta.split()[0]
rows=[]
with tarfile.open(out/'windows-changes.tar.gz','w:gz') as tar:
 for name in sorted(changed):
  p=root/name
  if p.is_symlink():raise RuntimeError('Unexpected source symlink '+name)
  if not p.exists():rows.append({'path':name,'deleted':True});continue
  if not p.is_file():raise RuntimeError('Unexpected path '+name)
  b=p.read_bytes();row={'path':name,'size':len(b),'sha256':hashlib.sha256(b).hexdigest(),'mode':mode.get(name,'100644')};rows.append(row)
  tar.add(p,arcname=name,recursive=False)
(out/'working-tree.patch').write_bytes(git('diff','--binary','HEAD'))
(out/'staged.patch').write_bytes(git('diff','--cached','--binary'))
for row in rows:
 if not row.get('deleted') and hashlib.sha256((root/row['path']).read_bytes()).hexdigest()!=row['sha256']:raise RuntimeError('Source changed during capture: '+row['path'])
v={'head':head,'branch':git('branch','--show-current').decode().strip(),'remote':git('remote','get-url','origin').decode().strip(),'status':git('status','--porcelain=v1').decode(),'files':rows,'created_unix':time.time(),'working_tree_not_modified':True}
(out/'inventory.json').write_text(json.dumps(v,indent=2)+'\n')
print(json.dumps({'head':head,'changed_files':len(rows),'archive':str(out/'windows-changes.tar.gz'),'bytes':(out/'windows-changes.tar.gz').stat().st_size}))
