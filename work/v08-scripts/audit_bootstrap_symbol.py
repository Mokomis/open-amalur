"""Windows-only diagnostic: exact symbol uses/writes in frozen v05 IR.

Does not execute scripts, import modules, infer init ordering, or turn arbitrary
named calls into require edges. Origins are only tracked within each IR block.
"""
import argparse,hashlib,json,platform,re
from pathlib import Path
assert platform.system()=='Windows'
root=Path.home()/'Documents/Opem Amalur'
parser=argparse.ArgumentParser();parser.add_argument('--symbol',default='parent')
parser.add_argument('--draft-root',type=Path,default=root/'outputs/initial-corpus-drafts-v05')
parser.add_argument('--output',type=Path,default=root/'outputs/scene-v08/audit/bootstrap-symbol.json')
parser.add_argument('--maximum-scripts',type=int,default=4096)
args=parser.parse_args();assert re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]{0,127}',args.symbol)
assert 1<=args.maximum_scripts<=4096
manifest=json.loads((args.draft_root/'manifest.json').read_text(encoding='utf-8-sig'))
entries=manifest['unique_scripts'];assert len(entries)<=args.maximum_scripts
def literal(text):
    try:value=json.loads(text)
    except (TypeError,ValueError):return None
    return value if isinstance(value,str) else None
def functions(fn):
    yield fn
    for child in fn.get('children',[]):yield from functions(child)
def operand(row,known):
    if not row:return None
    if row['kind']=='register':return known.get(row['index'])
    text=literal(row.get('lua'));return ('string',text) if text is not None else None
found=[];scanned=0
for digest,entry in sorted(entries.items()):
    directory=(args.draft_root/entry['directory']).resolve()
    assert directory.is_relative_to(args.draft_root.resolve())
    irpath=directory/'ir.json';data=irpath.read_bytes();assert len(data)<=128*1024*1024
    ir=json.loads(data.decode('utf-8-sig'));assert ir['input_sha256']==digest
    hits=[];module_calls=[]
    for fn in functions(ir['root_function']):
        rows={row['pc']:row for row in fn['instructions']}
        for block in fn['blocks']:
            known={}
            for pc in block['instruction_pcs']:
                row=rows[pc]
                if row.get('reachable') is False:continue
                kind=row.get('kind');a=row.get('A');value=None
                site={'function':fn['path'],'root_function':fn is ir['root_function'],
                      'pc':pc,'file_offset':row['file_offset'],'opcode':row['name']}
                if kind in ('getglobal','setglobal') and literal(row.get('constant_lua'))==args.symbol:
                    hits.append({**site,'operation':kind,'value_origin_in_block':known.get(a) if kind=='setglobal' else None,
                                 'limitation':'Closure environment may be module-local; SETGLOBAL alone is not a realm-global definition proof.'})
                if kind in ('setfield','setfield_cached','settable'):
                    key=('string',literal(row.get('field_key'))) if kind!='settable' else operand(row.get('key_operand'),known)
                    if key==('string',args.symbol):
                        hits.append({**site,'operation':'named_table_write','target_origin_in_block':known.get(a),
                                     'value_origin_in_block':operand(row.get('value_operand'),known)})
                if kind in ('getfield_k','getfield_cached_k') and literal(row.get('constant_lua'))==args.symbol:
                    hits.append({**site,'operation':'named_table_read','target_origin_in_block':known.get(row.get('B'))})
                callee=known.get(a)
                if kind in ('call_fixed','call_cached_fixed','tailcall','tailcall_cached') and callee:
                    if callee==('global',args.symbol):
                        hits.append({**site,'operation':'direct_symbol_call','first_argument_in_block':known.get(a+1),
                                     'second_argument_in_block':known.get(a+2),'argument_count_field':row.get('B')})
                    if callee==('global','module'):
                        module_calls.append({**site,'first_argument_in_block':known.get(a+1)})
                    if callee==('global','rawset') and row.get('B',0)>=4 and known.get(a+2)==('string',args.symbol):
                        hits.append({**site,'operation':'rawset_named_candidate','target_origin_in_block':known.get(a+1),
                                     'value_origin_in_block':known.get(a+3),'argument_count_field':row.get('B')})
                if kind=='getglobal':value=('global',literal(row.get('constant_lua')))
                elif kind=='loadk':
                    text=literal(row.get('constant_lua'))
                    if text is not None:value=('string',text)
                elif kind=='move':value=known.get(row.get('B'))
                elif kind=='closure':value=('closure_child',row.get('child_index'),pc)
                for register in set(row.get('writes',[]))|set(row.get('may_writes',[]))|set(row.get('kills',[])):
                    known.pop(register,None)
                if value is not None:known[a]=value
    if hits:
        found.append({'input_sha256':digest,'ir_path':str(irpath),'ir_sha256':hashlib.sha256(data).hexdigest(),
                      'module_calls':module_calls,'sites':hits})
    scanned+=1
report={'scope':'Exact symbol diagnostic from frozen IR; no execution, module aliases, bootstrap ordering or global-visibility proof.',
        'symbol':args.symbol,'scripts_scanned':scanned,'scripts_with_sites':len(found),'hits':found,
        'limitations':['Origins tracked only inside individual basic blocks; no interprocedural or cross-block inference.',
                       'Function bodies may never execute. Module calls can change closure environments.',
                       'Computed field names/rawset aliases/dynamic exports may be absent. No claim of all possible definitions.']}
encoded=json.dumps(report,indent=2)+'\n';assert len(encoded.encode())<=8*1024*1024
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(encoded,encoding='utf-8')
print(json.dumps({'output':str(args.output),'scripts_scanned':scanned,'scripts_with_sites':len(found)}))
