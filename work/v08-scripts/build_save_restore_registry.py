"""Windows-only SAVE_RESTORE namespace registry extension from exact native evidence."""
import argparse,copy,hashlib,json,platform,re
from pathlib import Path
SHA='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
COUNTS={'QUEST':48,'GAME':165,'ACTOR':611,'TIME':6,'WINDOW':232,'INPUT':42,'PROFILE':123}
def require(condition,message):
    if not condition:raise ValueError(message)
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def sha(data):return hashlib.sha256(data).hexdigest()
def namespace_lines(name,rows):
    return ['  [%s] = {'%json.dumps(name)]+['    [%s] = %s,'%(json.dumps(row['name']),json.dumps(row['callback'])) for row in rows]+['  },']
def main():
    require(platform.system()=='Windows','Generate the registry on Windows')
    parser=argparse.ArgumentParser()
    for name in ('base-manifest','base-lua','descriptors','owner-discovery','getter','output-dir'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();base=read(args.base_manifest);desc=read(args.descriptors);owner=read(args.owner_discovery)
    wrapped=read(args.getter);getter=wrapped.get('structuredContent',wrapped)
    require(base['target_sha256']==desc['target_sha256']==owner['target_sha256']==getter['subject']['digest']['sha256']==SHA,'Native target SHA differs')
    require(set(base['namespaces'])==set(COUNTS),'Exactly seven proven base namespaces required')
    expected=['-- Generated from Windows native descriptor evidence; addresses are metadata only.','-- No game function is called by loading this registry.','return {']
    for name,namespace in base['namespaces'].items():
        require(namespace['count']==len(namespace['methods'])==COUNTS[name],'Base count differs: '+name)
        expected+=namespace_lines(name,namespace['methods'])
    expected.append('}')
    base_bytes=args.base_lua.read_bytes();base_lua=base_bytes.decode('utf-8-sig')
    require(base_lua.replace('\r\n','\n')=='\n'.join(expected)+'\n','Base Lua does not exactly match all seven manifest namespaces')
    require(int(desc['entry'],0)==0xec14b0,'Wrong SAVE_RESTORE initializer')
    rows=desc['descriptors']
    require(len(rows)==len({r['name'] for r in rows})==41,'Need41 unique SAVE_RESTORE descriptors')
    require(desc['allocation_count_argument']['count']==41,'Native allocation count is not41')
    for row in rows:
        require(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',row['name']),'Unsafe method name')
        require(isinstance(row['callback'],str) and re.fullmatch(r'0x[0-9a-f]+',row['callback']),'Missing callback')
        require(row['callback_stack_offset']==row['name_object_stack_offset']+12,'Callback stack layout differs')
    callbacks={row['name']:row['callback'] for row in rows}
    require(callbacks.get('does_platform_support_quick_save')=='0xe2ab60','Quick-save capability callback differs')
    owners=[r for r in owner['owner_rtti'] if r['name']=='.?AVLuaSaveRestoreServices@BHG@@']
    require(len(owners)==1 and len(owners[0]['vtables'])==1,'SAVE_RESTORE owner RTTI is ambiguous')
    table=owners[0]['vtables'][0]
    require(table['object_offset']==0 and int(table['vtable'],0)==0x174a608,'Wrong SAVE_RESTORE owner primary vtable')
    require([int(x,0) for x in table['first_six_slots']]==[0xea4690,0xaab570,0xaab580,0xea4670,0xaab590,0xec14b0],'SAVE_RESTORE owner slots differ')
    require(int(getter['parameters']['procedure'],0)==0xea4670,'Wrong namespace getter')
    require(re.search(r'FUN_00af4d40\s*\(\s*"SAVE_RESTORE"\s*\)',getter['normalized_result']),'Getter does not construct SAVE_RESTORE')
    newline='\r\n' if '\r\n' in base_lua else '\n';close=base_lua.rfind('}');prefix=base_lua[:close]
    generated=prefix+newline.join(namespace_lines('SAVE_RESTORE',rows))+newline+base_lua[close:]
    output=args.output_dir;output.mkdir(parents=True,exist_ok=True)
    lua_path=output/'engine_binding_registry.lua';lua_path.write_bytes(generated.encode('utf-8'))
    extended=copy.deepcopy(base);extended['namespaces']['SAVE_RESTORE']={
        'registration_function':'0xec14b0','count':41,'descriptor_evidence':str(args.descriptors),
        'descriptor_evidence_sha256':sha(args.descriptors.read_bytes()),
        'namespace_association':'Observed owner slots3/5 associate SAVE_RESTORE getter and descriptor initializer. No save_restore behavior implemented by registry.',
        'namespace_owner':{'vtable':'0x174a608','getter':'0xea4670','getter_slot':'0x174a614','registration_slot':'0x174a61c','getter_evidence_id':getter['evidence_id'],'owner_evidence':str(args.owner_discovery)},
        'mapping_status':'Observed descriptor names and callbacks paired by normalized stack offsets','methods':rows}
    (output/'engine-binding-registry.json').write_text(json.dumps(extended,indent=2)+'\n',encoding='utf-8')
    receipt={'target_sha256':SHA,'scope':'41 native SAVE_RESTORE method registrations only. No save capability, storage, persistence, or native parity implemented.',
        'namespace_counts':{name:v['count'] for name,v in extended['namespaces'].items()},
        'base_seven_tables_preserved':generated.startswith(prefix),'base_source_sha256':sha(base_bytes),
        'output_source_sha256':sha(lua_path.read_bytes()),'preserved_prefix_sha256':sha(prefix.encode('utf-8')),
        'inputs':{name:{'path':str(getattr(args,name)),'sha256':sha(getattr(args,name).read_bytes())} for name in ('base_manifest','base_lua','descriptors','owner_discovery','getter')},
        'generator_sha256':sha(Path(__file__).read_bytes())}
    (output/'save-restore-registry-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
