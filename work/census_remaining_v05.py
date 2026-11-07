import collections,json
from pathlib import Path
root=Path.home()/'Documents'/'Opem Amalur'
full=root/'outputs/initial-corpus-drafts-v04'
opcodes=collections.Counter();reason_counts=collections.Counter(); examples=collections.defaultdict(list)
records=[]
def visit(fn):
    yield fn
    for child in fn['children']:yield from visit(child)
manifest=json.loads((full/'manifest.json').read_text())
for record in manifest['records']:
    if record['status']!='exported' or not record['summary']['unresolved_function_bodies']:continue
    ir=json.loads((full/Path(record['file']).stem/'ir.json').read_text())
    for fn in visit(ir['root_function']):
        if fn['body_emittable']:continue
        reasons={u['reason'] for u in fn['unknowns']}
        missing={(r['opcode'],r['name']) for r in fn['instructions'] if r['status']=='unknown' and r['reachable'] is not False}
        opcodes.update(missing);reason_counts.update(reasons)
        entry={'file':record['file'],'name':record['name'],'input_sha256':ir['input_sha256'],'path':fn['path'],
               'instructions':len(fn['instructions']),'unknowns':fn['unknowns'],'function':fn}
        records.append({k:v for k,v in entry.items() if k!='function'})
        for key in list(reasons)+['opcode:'+str(n)+':'+name for n,name in missing]:
            bucket=examples[key];bucket.append(entry);bucket.sort(key=lambda e:e['instructions']);del bucket[5:]
report={'unresolved_bodies':len(records),'opcode_body_counts':[{'opcode':op,'name':name,'bodies':count} for (op,name),count in opcodes.most_common()],
        'reason_counts':dict(reason_counts),'examples':dict(examples),'records':records}
out=root/'outputs/remaining-v05/census.json';out.write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('examples','records')},indent=2))
