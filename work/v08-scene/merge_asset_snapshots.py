"""Merge selected name-hash snapshots only when every duplicate agrees."""
from pathlib import Path
import argparse,struct,json,hashlib,platform
assert platform.system()=='Windows'
ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--glob',required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
files=sorted(args.root.glob(args.glob));assert files and len(files)<=64
by_hash={};by_id={};records=[];duplicates=0
for p in files:
 data=p.read_bytes();assert len(data)>=8
 version,count=struct.unpack_from('<II',data);assert version==1 and count<=65536 and len(data)==8+count*8
 values=struct.unpack_from('<'+str(count*2)+'I',data,8);ids=values[:count];hashes=values[count:]
 # Identical repeated pairs are harmless; both-direction checks below reject
 # conflicting IDs or hashes within a file as well as across archives.
 for identifier,key in zip(ids,hashes):
  assert identifier!=0
  if key in by_hash and by_hash[key]!=identifier:raise ValueError(f'hash conflict {key} in {p}')
  if identifier in by_id and by_id[identifier]!=key:raise ValueError(f'ID name conflict {identifier} in {p}')
  if key in by_hash:duplicates+=1
  by_hash[key]=identifier;by_id[identifier]=key
 records.append({'file':str(p),'sha256':hashlib.sha256(data).hexdigest(),'entries':count})
assert 0<len(by_id)<=65536
pairs=sorted(by_id.items());result=struct.pack('<II',1,len(pairs))+struct.pack('<'+str(len(pairs))+'I',*(i for i,h in pairs))+struct.pack('<'+str(len(pairs))+'I',*(h for i,h in pairs))
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(result)
report={'scope':'Union of exact agreeing ID/hash pairs; no archive precedence assumed; conflicts reject entire merge','source_files':records,'entries':len(pairs),'agreeing_duplicates':duplicates,'output_sha256':hashlib.sha256(result).hexdigest()}
args.output.with_suffix('.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
