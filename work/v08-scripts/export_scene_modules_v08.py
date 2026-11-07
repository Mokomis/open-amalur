"""Windows-only explicit module inventory from existing frozen v0.5 drafts.

Dependencies are conservative literal require/parent calls within individual IR basic
blocks. They are not a complete dependency proof and do not resolve dynamic
names, runtime overrides, aliases across blocks, or archive precedence.
"""
import argparse,hashlib,json,platform,re
from collections import defaultdict,deque
from pathlib import Path
from module_source_adapter import adapt_source
PARENT_INPUT_SHA='29df50b90af3955046a530292163bce959e4f6248edadc1b53865c349cde042c'
PARENT_FROZEN_NORMALIZED_SHA='b2146e4c32633e7519193687304f4d000592ff7bdb3c95b08cdcd3bbd943d762'

def validate_parent_utils(digest,ir,source):
    normalized=source.replace('\r\n','\n')
    if digest!=PARENT_INPUT_SHA or hashlib.sha256(normalized.encode('utf-8')).hexdigest()!=PARENT_FROZEN_NORMALIZED_SHA:
        raise ValueError('ParentUtils original identity or frozen-source contract differs')
    rows={r['pc']:r for r in ir['root_function']['instructions']}
    expected={2:('loadk','"ParentUtils"',1),9:('getglobal','"require"',0),11:('setglobal','"my_req"',0),
              23:('getglobal','"_G"',0),25:('getglobal','"parent_internal"',1)}
    for pc,(kind,name,register) in expected.items():
        row=rows.get(pc,{})
        if row.get('kind')!=kind or row.get('constant_lua')!=name or row.get('A')!=register:
            raise ValueError('ParentUtils binding contract differs at pc'+str(pc))
    row=rows.get(27,{})
    if row.get('kind')!='setfield' or row.get('A')!=0 or row.get('field_key')!='"parent"' or row.get('value_operand')!={'kind':'register','index':1}:
        raise ValueError('ParentUtils no longer exports _G.parent=parent_internal')
    if ir['summary']['unresolved_function_bodies']!=0:
        raise ValueError('ParentUtils has unresolved bodies')
    return {'input_sha256':digest,'frozen_source_normalized_sha256':PARENT_FROZEN_NORMALIZED_SHA,
            'realm_export':{'table_load_pc':23,'function_load_pc':25,'setfield_pc':27,'name':'parent'},
            'host_condition':'no_dependency_require must remain absent so original my_req selects explicit require',
            'dependency_rule':'Only literal first arguments to direct block-local global parent calls; no name/path normalization.'}

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
                if kind in {'call_fixed','call_cached_fixed','tailcall','tailcall_cached'} and callee and callee[0]=='global' and callee[1] in {'require','parent'}:
                    classified.add((fn['path'],callee[2]))
                    arg=known.get(a+1);site={'function':fn['path'],'pc':pc,'file_offset':row['file_offset'],'dependency_load_pc':callee[2],'via':callee[1]}
                    if row.get('B',0)>=2 and arg and arg[0]=='string':found.append({**site,'module':arg[1]})
                    else:unknown.append({**site,'reason':'dependency target is not a block-local literal first argument'})
                if kind=='getglobal':
                    global_name=string_literal(row.get('constant_lua'));value=('global',global_name,pc)
                    if global_name in {'require','parent'}:references[(fn['path'],pc)]={'function':fn['path'],'pc':pc,'file_offset':row['file_offset'],'via':global_name}
                elif kind=='loadk':
                    literal=string_literal(row.get('constant_lua'))
                    if literal is not None:value=('string',literal)
                elif kind=='move':value=known.get(row.get('B'))
                for register in set(row.get('writes',[]))|set(row.get('may_writes',[]))|set(row.get('kills',[])):known.pop(register,None)
                if value is not None:known[a]=value
    unknown.extend({**site,'reason':'dependency reference not classified as a block-local direct call'} for key,site in references.items() if key not in classified)
    return found,unknown

SELECTION_REASON='Explicit preview module identity selected by --select-module; not native archive precedence or variant equivalence.'
def valid_module_name(name):
    return isinstance(name,str) and bool(name) and len(name.encode('utf-8'))<=255 and not any(ord(c)<32 or ord(c)==127 or c in '/\\:' for c in name)
def parse_selections(values):
    if len(values)>256:raise ValueError('Too many explicit module selections')
    selected={}
    for value in values:
        if not isinstance(value,str) or value.count('=')!=1:raise ValueError('Selection must be NAME=SHA256')
        name,digest=value.split('=',1)
        if not valid_module_name(name) or re.fullmatch(r'[0-9a-fA-F]{64}',digest) is None:raise ValueError('Invalid selected module name or SHA256')
        if name in selected:raise ValueError('Duplicate explicit module selection: '+name)
        digest=digest.lower()
        if name=='ParentUtils' and digest!=PARENT_INPUT_SHA:raise ValueError('ParentUtils selection conflicts with pinned identity')
        selected[name]=digest
    return selected

def select_candidate(name,matches,selections):
    identities={r['sha256'] for r in matches};digest=selections.get(name)
    if digest is not None and digest not in identities:
        raise ValueError('Selected SHA256 is not an exact candidate for '+name)
    ambiguity=None;receipt=None
    if len(identities)>1:
        ambiguity={'module':name,'candidates':matches,'resolution':'explicit_preview_selection' if digest else 'unresolved',
                   'selected_input_sha256':digest,'reason':SELECTION_REASON if digest else 'No explicit identity selection; variants remain excluded.'}
    if digest is not None:
        # Duplicated filenames with identical input bytes are one identity.
        chosen=next(r for r in matches if r['sha256']==digest)
        receipt={'module':name,'input_sha256':digest,'input_file':chosen['file'],
                 'reason':SELECTION_REASON,'candidate_identities':sorted(identities),
                 'unselected_input_sha256':sorted(identities-{digest})}
    elif len(identities)==1:chosen=matches[0]
    else:chosen=None
    return chosen,ambiguity,receipt

def main():
    assert platform.system()=='Windows','fresh corpus processing runs on Windows'
    root=Path.home()/'Documents'/'Opem Amalur'
    ap=argparse.ArgumentParser();ap.add_argument('--module',action='append',dest='roots',default=[])
    ap.add_argument('--index',type=Path,default=root/'outputs/scene-v07/standalone-name-index.json')
    ap.add_argument('--output',type=Path,default=root/'outputs/scene-v08/modules-parent-candidate')
    ap.add_argument('--maximum',type=int,default=256)
    ap.add_argument('--select-module',action='append',default=[],metavar='NAME=SHA256',help='Explicit preview identity; does not infer archive precedence')
    ap.add_argument('--maximum-source-bytes',type=int,default=16*1024*1024)
    ap.add_argument('--maximum-total-source-bytes',type=int,default=128*1024*1024);args=ap.parse_args()
    selections=parse_selections(args.select_module)
    roots=args.roots or ['ParentUtils','SpaceCommon'];full=root/'outputs/initial-corpus-drafts-v05'
    if 'ParentUtils' not in roots:raise ValueError('Explicit pinned ParentUtils inventory root is required')
    if not 1<=args.maximum<=256 or not 1<=args.maximum_source_bytes<=16*1024*1024 or not 1<=args.maximum_total_source_bytes<=128*1024*1024:raise ValueError('Export bounds exceed selected profile')
    manifest=json.loads((full/'manifest.json').read_text(encoding='utf-8-sig'))
    index=json.loads(args.index.read_text(encoding='utf-8-sig'));by_name=defaultdict(list)
    for record in index:
        if isinstance(record.get('name'),str):by_name[record['name']].append(record)
    for name in selections:select_candidate(name,by_name.get(name,[]),selections)
    if args.output.exists() and any(args.output.iterdir()):raise ValueError('Use a new empty candidate output directory; existing inventories are preserved')
    args.output.mkdir(parents=True,exist_ok=True);original=args.output/'original';original.mkdir(exist_ok=True)
    total_source_bytes=0;parent_contract=None
    queue=deque(roots);seen=set();records=[];missing=[];ambiguous=[];selection_receipts=[];lines=['# Exact module name<TAB>generated source basename. No implicit search paths.']
    while queue:
        name=queue.popleft()
        if name in seen:continue
        if not valid_module_name(name):
            raise ValueError('Module name is outside the explicit host-name domain: '+repr(name))
        seen.add(name)
        if len(seen)>args.maximum:raise ValueError('Module dependency selection exceeds explicit bound')
        matches=by_name.get(name,[]);identities={r['sha256'] for r in matches}
        if not matches:
            missing.append({'module':name,'case_candidates':[n for n in by_name if n.casefold()==name.casefold()]});continue
        record,ambiguity,selection=select_candidate(name,matches,selections)
        if ambiguity:ambiguous.append(ambiguity)
        if record is None:continue
        if selection:selection_receipts.append(selection)
        digest=record['sha256'];source=full/manifest['unique_scripts'][digest]['directory']
        if not source.resolve().is_relative_to(full.resolve()):raise ValueError('Draft directory escapes inventory')
        frozen=source/'whole-script.lua'
        if frozen.stat().st_size>args.maximum_source_bytes:raise ValueError('Frozen source byte bound exceeded before read')
        ir_path=source/'ir.json'
        if ir_path.stat().st_size>128*1024*1024:raise ValueError('IR diagnostic byte bound exceeded')
        ir=json.loads(ir_path.read_text(encoding='utf-8-sig'));assert ir['input_sha256']==digest
        data=frozen.read_bytes();text=data.decode('utf-8-sig')
        if digest not in text:raise ValueError('Generated source input identity differs from manifest')
        if name=='ParentUtils':parent_contract=validate_parent_utils(digest,ir,text)
        adapted,admission=adapt_source(text);filename=digest+'.lua';dest=args.output/filename
        encoded=adapted.encode('utf-8')
        if len(encoded)>args.maximum_source_bytes or total_source_bytes+len(encoded)>args.maximum_total_source_bytes:raise ValueError('Export source byte bound exceeded')
        total_source_bytes+=len(encoded);dest.write_bytes(encoded);(original/filename).write_bytes(data)
        calls,unknown=dependencies(ir);queue.extend(c['module'] for c in calls)
        lines.append(name+'\t'+filename)
        records.append({'module':name,'input_file':record['file'],'input_sha256':digest,
                        'frozen_source_sha256':sha(frozen),'adapted_source_sha256':sha(dest),
                        'source_file':filename,'source_bytes':len(encoded),'admission':admission,
                        'literal_require_calls':[c for c in calls if c['via']=='require'],
                        'literal_parent_calls':[c for c in calls if c['via']=='parent'],
                        'unresolved_require_calls':[c for c in unknown if c['via']=='require'],
                        'unresolved_parent_calls':[c for c in unknown if c['via']=='parent'],'function_bodies':ir['summary']['functions']})
    unused=set(selections)-{r['module'] for r in selection_receipts}
    if unused:raise ValueError('Explicit selections outside exported dependency closure: '+', '.join(sorted(unused)))
    if parent_contract is None:raise ValueError('Pinned ParentUtils export was missing or ambiguous')
    (args.output/'modules.tsv').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    report={'scope':'Explicit wrapper names plus block-local literal require/parent dependencies under pinned ParentUtils; explicit SHA selections retain all ambiguity records; no aliases, runtime order or archive-variant equivalence claim.',
            'roots':roots,'required_bootstrap_module':'ParentUtils','parent_utils_contract':parent_contract,
            'total_source_bytes':total_source_bytes,'maximum_modules':args.maximum,
            'maximum_source_bytes':args.maximum_source_bytes,'maximum_total_source_bytes':args.maximum_total_source_bytes,
            'literal_parent_dependency_sites':sum(len(r['literal_parent_calls']) for r in records),'registered_modules':len(records),'function_bodies':sum(r['function_bodies'] for r in records),
            'missing':missing,'ambiguous':ambiguous,
            'unresolved_ambiguous':[r for r in ambiguous if r['resolution']=='unresolved'],
            'explicit_module_selections':selection_receipts,'modules':records,
            'manifest_sha256':sha(args.output/'modules.tsv'),'source_adapter_sha256':sha(Path(__file__).with_name('module_source_adapter.py'))}
    (args.output/'module-inventory.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='modules'},indent=2))

if __name__=='__main__':main()
