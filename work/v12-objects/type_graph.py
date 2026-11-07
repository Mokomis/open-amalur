from pathlib import Path
import json,struct,csv,hashlib,sys,collections
r=Path.home()/'Documents/Opem Amalur';sys.path.insert(0,str(r/'src'));from amalur_script import inspect_bundle_bytes,Limits
report=json.loads((r/'outputs/scene-v12/type-members.json').read_text());records={};origins={}
for row in report['batches']:
 p=r/'work/scene-inputs-v09'/row['archive']/row['file'];b=p.read_bytes()
 if hashlib.sha256(b).hexdigest()!=row['sha256']:raise ValueError('Batch changed')
 directory=inspect_bundle_bytes(b,Limits(max_bundle_members=32768))
 for x in directory['directory']:
  at=x['member_file_offset'];raw=b[at:at+x['declared_member_bytes']];key=x['resource_id']
  if key in records and raw!=records[key]:raise ValueError(f'Conflicting same-type definitions {key}')
  records[key]=raw;origins.setdefault(key,dict(batch=row['file'],archive=row['archive'],offset=at,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
symbols=r/'references/ZucchiniZap--AmalurBxmlConverter/bin/Release/net10.0-windows/symbol_tables'
types={int(x['id']):x['value'] for x in csv.DictReader((symbols/'simtype.csv').open(encoding='utf-8-sig'))};scripts={int(x['id']):x['value'] for x in csv.DictReader((symbols/'luascript.csv').open(encoding='utf-8-sig'))}
queue=collections.deque(report['wanted']);nodes={};missing=[]
while queue:
 key=queue.popleft()
 if key in nodes or key in missing:continue
 if len(nodes)>128:raise ValueError('Ancestor scope cap')
 raw=records.get(key)
 if raw is None:missing.append(key);continue
 if len(raw)<20:raise ValueError(f'Unadmitted short type {key}')
 parent,flags,u8,u12,script=struct.unpack_from('<5I',raw)
 nodes[key]=dict(type_id=key,name=types.get(key),parent_candidate=parent,flags_unknown=flags,unknown8=u8,unknown12=u12,script_candidate=script,script_name=scripts.get(script),source=origins[key],tail_hex=raw[20:].hex())
 if parent not in (0,1,0xffffffff):queue.append(parent)
script_ids=sorted({n['script_candidate'] for n in nodes.values() if n['script_name']})
o=dict(scope='Candidate fixed prefix from selected SimType batch members: parent/type and Lua script IDs corroborated by symbol names; native per-field reader pending',root_types=report['wanted'],nodes=list(nodes.values()),missing=missing,script_ids=script_ids,scripts=[dict(id=x,name=scripts[x]) for x in script_ids])
(r/'outputs/scene-v12/type-graph.json').write_text(json.dumps(o,indent=2));print(json.dumps(dict(nodes=len(nodes),missing=missing,scripts=o['scripts']),indent=2))
