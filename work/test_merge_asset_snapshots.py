import json,struct,subprocess,sys,tempfile,platform
from pathlib import Path
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';records=[]
def data(pairs):return struct.pack('<II',1,len(pairs))+b''.join(struct.pack('<I',i)for i,h in pairs)+b''.join(struct.pack('<I',h)for i,h in pairs)
for label,pairs1,pairs2,okay,expected in [('identical-within',[(1,2),(1,2)],[],True,1),('identical-across',[(1,2)],[(1,2),(3,4)],True,2),('id-conflict',[(1,2)],[(1,4)],False,0),('hash-conflict',[(1,2)],[(3,2)],False,0),('within-id-conflict',[(1,2),(1,3)],[],False,0)]:
 with tempfile.TemporaryDirectory(prefix='opem-catalog-') as td:
  td=Path(td);(td/'a.bin').write_bytes(data(pairs1));(td/'b.bin').write_bytes(data(pairs2));out=td/'out'/'merged.bin'
  p=subprocess.run([sys.executable,str(r/'work/merge_asset_snapshots.py'),'--root',str(td),'--glob','*.bin','--output',str(out)],capture_output=True,timeout=15)
  assert (p.returncode==0)==okay,(label,p.stderr)
  if okay:assert struct.unpack_from('<I',out.read_bytes(),4)[0]==expected
  else:assert not out.exists()
  records.append({'case':label,'passed':True})
report={'ok':True,'checks':len(records),'records':records};(r/'outputs/scene-v08/catalog-merge-tests.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
