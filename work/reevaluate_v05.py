"""Read-only Windows corpus reconstruction census; preserve every entry identity."""
from pathlib import Path
import json,sys,collections,platform,hashlib,time
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur'
sys.path.insert(0,str(root/'src'))
from amalur_script import parse_file,iter_bundle_file
from amalur_reconstruct import lift_function
profile=json.loads((root/'outputs/native-script-profile.json').read_text())
source=root/'work/initial-script-corpus-v04';out=root/'outputs/remaining-v05'
reasons=collections.Counter();opcodes=collections.Counter();examples=collections.defaultdict(list);records=[];errors=[];unique={};totals=collections.defaultdict(collections.Counter)
def visit(f):
 yield f
 for c in f['children']:yield from visit(c)
def process(parsed,label,group):
 h=parsed['input_sha256']
 if h not in unique:
  ir=lift_function(parsed['chunk']['root_function'],'0',profile);fs=list(visit(ir))
  counts={'functions':len(fs),'supported':sum(f['body_emittable'] for f in fs)}
  counts['unresolved']=counts['functions']-counts['supported'];unique[h]=counts
  for f in fs:
   if f['body_emittable']:continue
   rr=set(u['reason'] for u in f['unknowns']);reasons.update(rr)
   oo={(r['opcode'],r['name']) for r in f['instructions'] if r['status']=='unknown' and r['reachable'] is not False};opcodes.update(oo)
   e={'label':label,'input_sha256':h,'path':f['path'],'instructions':len(f['instructions']),'unknowns':f['unknowns'],'function':f}
   for key in rr|{f'opcode:{op}:{name}' for op,name in oo}:
    bucket=examples[key];bucket.append(e);bucket.sort(key=lambda x:x['instructions']);del bucket[4:]
 counts=unique[h];totals[group].update(counts)
 records.append({'label':label,'group':group,'input_sha256':h,'container':parsed.get('container'),**counts})
for i,path in enumerate(sorted(source.glob('*.lua_bxml'))):
 try:
  if path.name.startswith('batch'):
   for member in iter_bundle_file(path):process(member,path.name+':'+str(member['container']['index']),'bundle')
  else:process(parse_file(path),path.name,'standalone')
 except Exception as e:errors.append({'file':path.name,'error':str(e)})
 if i%250==0:print(i,dict(totals),flush=True)
result={'totals':{k:dict(v) for k,v in totals.items()},'unique_inputs':len(unique),'unique_totals':dict(sum((collections.Counter(v) for v in unique.values()),collections.Counter())),
 'reason_counts':dict(reasons),'opcode_counts':[{'opcode':k[0],'name':k[1],'bodies':v} for k,v in opcodes.most_common()], 'errors':errors,'examples':dict(examples),'records':records}
(out/'reevaluation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('examples','records')},indent=2))
