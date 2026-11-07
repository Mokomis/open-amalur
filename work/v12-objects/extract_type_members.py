from pathlib import Path
import sys,json,subprocess,hashlib
r=Path.home()/'Documents/Opem Amalur';sys.path.insert(0,str(r/'src'));from amalur_script import inspect_bundle_bytes,Limits
p=r/'outputs/initial-archive-list.txt';data=p.read_bytes();lines=data.decode('utf-16' if data.startswith(b'\xff\xfe') else 'utf-8-sig').splitlines();names=[s.strip() for s in lines if s.strip().startswith('batch_') and s.strip().endswith('.simtype_bxml')];assert 1<=len(names)<=32
subprocess.run([sys.executable,str(r/'work/v09-scene/extract_scene_inputs.py'),*names],check=True,stdout=subprocess.DEVNULL)
inv=json.loads((r/'outputs/scene-v12/actor-candidates.json').read_text());wanted={m['id'] for rec in inv['records'] for m in rec['matches'] if m['offset']==56 and m['kind']=='simtype'}
selected=[];batches=[];out=r/'work/v12-objects/simtype-members';out.mkdir(exist_ok=True);total=0
for archive in ['initial_0.pak','DATA_0.pak','patch_0.pak']:
 for name in names:
  path=r/'work/scene-inputs-v09'/archive/name
  if not path.exists():continue
  b=path.read_bytes();total+=len(b)
  if total>256*1024*1024:raise ValueError('Batch aggregate cap')
  directory=inspect_bundle_bytes(b,Limits(max_bundle_members=32768));batches.append(dict(archive=archive,file=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),members=directory['member_count']))
  for entry in directory['directory']:
   if entry['resource_id'] not in wanted:continue
   at=entry['member_file_offset'];n=entry['declared_member_bytes'];raw=b[at:at+n];dest=out/archive/name;dest.mkdir(parents=True,exist_ok=True);target=dest/(str(entry['resource_id'])+'.simtype_bxml')
   if target.exists() and target.read_bytes()!=raw:raise ValueError('Preserve existing differing member')
   target.write_bytes(raw);selected.append(dict(resource_id=entry['resource_id'],source_archive=archive,source_batch=name,source_batch_sha256=directory['input_sha256'],member_file_offset=at,member_bytes=n,member_sha256=hashlib.sha256(raw).hexdigest(),output=str(target),first64_hex=raw[:64].hex()))
report=dict(scope='Observed generic batch directory reused for exact bounded member extraction; SimType payload semantics pending',batches=batches,wanted=sorted(wanted),selected=selected,missing=sorted(wanted-{x['resource_id'] for x in selected}));(r/'outputs/scene-v12/type-members.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(batches=len(batches),wanted=len(wanted),selected=len(selected),missing=report['missing'],samples=selected[:2]),indent=2))
