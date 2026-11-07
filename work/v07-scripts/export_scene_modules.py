"""Windows-only explicit module inventory from existing frozen v0.5 drafts.

Dependencies are conservative literal require calls within individual IR basic
blocks. They are not a complete dependency proof and do not resolve dynamic
names, runtime overrides, aliases across blocks, or archive precedence.
"""
import argparse,hashlib,json,platform
from collections import defaultdict,deque
from pathlib import Path
from module_source_adapter import adapt_source

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def string_literal(text):
    try:value=json.loads(text)
    except (TypeError,ValueError):return None
    return value if isinstance(value,str) else None
def functions(fn):
    yield fn
    for child in fn.get('children',[]):yield from functions(child)
def dependencies(ir):
    found=[];unknown=[];references={};classified=set()
    for fn in functions(ir['root_function']):
        rows={r['pc']:r for r in fn['instructions']}
        for block in fn['blocks']:
            known={}
            for pc in block['instruction_pcs']:
                row=rows[pc]
                if row.get('reachable') is False:continue
                kind=row.get('kind');a=row.get('A');value=None
                callee=known.get(a)
                if kind in {'call_fixed','call_cached_fixed','tailcall','tailcall_cached'} and callee and callee[:2]==('global','require'):
                    classified.add((fn['path'],callee[2]))
                    arg=known.get(a+1);site={'function':fn['path'],'pc':pc,'file_offset':row['file_offset'],'require_load_pc':callee[2]}
                    if row.get('B',0)>=2 and arg and arg[0]=='string':found.append({**site,'module':arg[1]})
                    else:unknown.append({**site,'reason':'require target is not a block-local literal first argument'})
                if kind=='getglobal':
                    global_name=string_literal(row.get('constant_lua'));value=('global',global_name,pc)
                    if global_name=='require':references[(fn['path'],pc)]={'function':fn['path'],'pc':pc,'file_offset':row['file_offset']}
                elif kind=='loadk':
                    literal=string_literal(row.get('constant_lua'))
                    if literal is not None:value=('string',literal)
                elif kind=='move':value=known.get(row.get('B'))
                for register in set(row.get('writes',[]))|set(row.get('may_writes',[]))|set(row.get('kills',[])):known.pop(register,None)
                if value is not None:known[a]=value
    unknown.extend({**site,'reason':'require reference not classified as a block-local direct call'} for key,site in references.items() if key not in classified)
    return found,unknown

def main():
    assert platform.system()=='Windows','fresh corpus processing runs on Windows'
    root=Path.home()/'Documents'/'Opem Amalur'
    ap=argparse.ArgumentParser();ap.add_argument('--module',action='append',dest='roots',default=[])
    ap.add_argument('--index',type=Path,default=root/'outputs/scene-v07/standalone-name-index.json')
    ap.add_argument('--output',type=Path,default=root/'outputs/scene-v07/modules')
    ap.add_argument('--maximum',type=int,default=128);args=ap.parse_args()
    roots=args.roots or ['SpaceCommon'];full=root/'outputs/initial-corpus-drafts-v05'
    manifest=json.loads((full/'manifest.json').read_text(encoding='utf-8-sig'))
    index=json.loads(args.index.read_text(encoding='utf-8-sig'));by_name=defaultdict(list)
    for record in index:
        if isinstance(record.get('name'),str):by_name[record['name']].append(record)
    args.output.mkdir(parents=True,exist_ok=True);original=args.output/'original';original.mkdir(exist_ok=True)
    queue=deque(roots);seen=set();records=[];missing=[];ambiguous=[];lines=['# Exact module name<TAB>generated source basename. No implicit search paths.']
    while queue:
        name=queue.popleft()
        if name in seen:continue
        if not name or len(name.encode('utf-8'))>255 or any(ord(c)<32 or c in '/\\:' for c in name):
            raise ValueError('Module name is outside the explicit host-name domain: '+repr(name))
        seen.add(name)
        if len(seen)>args.maximum:raise ValueError('Module dependency selection exceeds explicit bound')
        matches=by_name.get(name,[]);identities={r['sha256'] for r in matches}
        if not matches:
            missing.append({'module':name,'case_candidates':[n for n in by_name if n.casefold()==name.casefold()]});continue
        if len(identities)!=1:
            ambiguous.append({'module':name,'candidates':matches});continue
        record=matches[0];digest=record['sha256'];source=full/manifest['unique_scripts'][digest]['directory']
        if not source.resolve().is_relative_to(full.resolve()):raise ValueError('Draft directory escapes inventory')
        ir=json.loads((source/'ir.json').read_text());assert ir['input_sha256']==digest
        frozen=source/'whole-script.lua';data=frozen.read_bytes();text=data.decode('utf-8-sig')
        if digest not in text:raise ValueError('Generated source input identity differs from manifest')
        adapted,admission=adapt_source(text);filename=digest+'.lua';dest=args.output/filename
        dest.write_text(adapted,encoding='utf-8');(original/filename).write_bytes(data)
        calls,unknown=dependencies(ir);queue.extend(c['module'] for c in calls)
        lines.append(name+'\t'+filename)
        records.append({'module':name,'input_file':record['file'],'input_sha256':digest,
                        'frozen_source_sha256':sha(frozen),'adapted_source_sha256':sha(dest),
                        'source_file':filename,'admission':admission,'literal_require_calls':calls,
                        'unresolved_require_calls':unknown,'function_bodies':ir['summary']['functions']})
    (args.output/'modules.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    report={'scope':'Explicit standalone wrapper-name inventory and conservative block-local literal requires; no engine behavior or archive-variant equivalence claim.',
            'roots':roots,'registered_modules':len(records),'function_bodies':sum(r['function_bodies'] for r in records),
            'missing':missing,'ambiguous':ambiguous,'modules':records,
            'manifest_sha256':sha(args.output/'modules.tsv'),'source_adapter_sha256':sha(Path(__file__).with_name('module_source_adapter.py'))}
    (args.output/'module-inventory.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='modules'},indent=2))

if __name__=='__main__':main()
