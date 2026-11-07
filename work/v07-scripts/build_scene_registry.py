"""Windows-only INPUT registry extension from explicit native evidence files."""
import argparse,copy,hashlib,json,platform,re,struct
from pathlib import Path
SHA='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
COUNTS={'QUEST':48,'GAME':165,'ACTOR':611,'TIME':6,'WINDOW':232}
def require(value,message):
    if not value:raise ValueError(message)
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def digest(data):return hashlib.sha256(data).hexdigest()
def namespace_lines(name,rows):
    return ['  [%s] = {'%json.dumps(name)]+['    [%s] = %s,'%(json.dumps(row['name']),json.dumps(row['callback'])) for row in rows]+['  },']
def main():
    require(platform.system()=='Windows','Generate the registry on Windows')
    parser=argparse.ArgumentParser()
    for name in ['base-manifest','base-lua','descriptors','vtable','getter','output-dir']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();base=read(args.base_manifest);descriptors=read(args.descriptors);vtable=read(args.vtable)
    wrapper=read(args.getter);getter=wrapper.get('structuredContent',wrapper)
    require(base['target_sha256']==descriptors['target_sha256']==vtable['target_sha256']==getter['subject']['digest']['sha256']==SHA,'Native target SHA mismatch')
    require(set(base['namespaces'])==set(COUNTS),'Expected exactly the frozen five base namespaces')
    expected=['-- Generated from Windows native descriptor evidence; addresses are metadata only.','-- No game function is called by loading this registry.','return {']
    for name,namespace in base['namespaces'].items():
        require(namespace['count']==len(namespace['methods'])==COUNTS[name],'Frozen namespace count mismatch: '+name)
        expected+=namespace_lines(name,namespace['methods'])
    expected.append('}');base_bytes=args.base_lua.read_bytes();base_lua=base_bytes.decode('utf-8-sig')
    require(base_lua.replace('\r\n','\n')=='\n'.join(expected)+'\n','Base registry source does not exactly match its descriptor manifest')
    require(int(descriptors['entry'],0)==0xed3500,'Wrong INPUT initializer')
    rows=descriptors['descriptors'];require(len(rows)==42 and len({row['name'] for row in rows})==42,'Need42 unique INPUT descriptors')
    require(descriptors['allocation_count_argument']['count']==42,'Native initializer allocation count must be42')
    for row in rows:
        require(re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',row['name']),'Invalid descriptor name')
        require(row['callback'] and re.fullmatch(r'0x[0-9a-f]+',row['callback']),'Missing callback address')
        require(row['callback_stack_offset']==row['name_object_stack_offset']+12,'Callback is not at descriptor+12')
    require({row['name']:row['callback'] for row in rows}.get('is_east_asian_controller_button_swap_required')=='0xe44b10','Input swap callback provenance differs')
    original_slots=None
    for span in vtable['ranges']:
        start=int(span['address'],0);data=bytes.fromhex(span['raw_hex']);offset=0x174a5e8-start
        if offset>=0 and offset+24<=len(data):original_slots=struct.unpack_from('<6I',data,offset);break
    require(original_slots==(0xea4330,0xaab570,0xaab580,0xea4310,0xaab590,0xed3500),'INPUT owner vtable slots do not match proof')
    require(int(getter['parameters']['procedure'],0)==0xea4310,'Wrong namespace getter')
    require(re.search(r'FUN_00af4d40\s*\(\s*"INPUT"\s*\)',getter['normalized_result']),'Getter does not explicitly name INPUT')
    newline='\r\n' if '\r\n' in base_lua else '\n';closing=base_lua.rfind('}')
    prefix=base_lua[:closing];generated=prefix+newline.join(namespace_lines('INPUT',rows))+newline+base_lua[closing:]
    output=args.output_dir;output.mkdir(parents=True,exist_ok=True)
    lua_path=output/'engine_binding_registry.lua';lua_path.write_bytes(generated.encode('utf-8'))
    extended=copy.deepcopy(base);extended['namespaces']['INPUT']={
        'registration_function':'0xed3500','count':42,'descriptor_evidence':str(args.descriptors),
        'descriptor_evidence_sha256':digest(args.descriptors.read_bytes()),
        'namespace_association':'Getter and initializer are slots3/5 of observed owner vtable; getter constructs INPUT. No input behavior implemented.',
        'namespace_owner':{'vtable':'0x174a5e8','getter':'0xea4310','getter_slot':'0x174a5f4','registration_slot':'0x174a5fc','getter_evidence_id':getter['evidence_id']},
        'mapping_status':'observed descriptor name and callback store paired by normalized stack offset','methods':rows}
    (output/'engine-binding-registry.json').write_text(json.dumps(extended,indent=2)+'\n',encoding='utf-8')
    receipt={'target_sha256':SHA,'scope':'Native INPUT method registry only; no controller-state implementation or native runtime parity claim.',
             'namespace_counts':{name:value['count'] for name,value in extended['namespaces'].items()},
             'base_five_tables_preserved':generated.startswith(prefix),'base_source_sha256':digest(base_bytes),
             'output_source_sha256':digest(lua_path.read_bytes()),'preserved_prefix_sha256':digest(prefix.encode('utf-8')),
             'inputs':{name:{'path':str(getattr(args,name)),'sha256':digest(getattr(args,name).read_bytes())} for name in ['base_manifest','base_lua','descriptors','vtable','getter']},
             'generator_sha256':digest(Path(__file__).read_bytes())}
    (output/'registry-extension-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))
if __name__=='__main__':main()
