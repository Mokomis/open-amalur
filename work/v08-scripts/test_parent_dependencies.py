"""Windows unit checks for exact block-local parent dependency inventory."""
import copy,importlib.util,json,platform
from pathlib import Path
assert platform.system()=='Windows'
path=Path(__file__).with_name('export_scene_modules_v08.py')
spec=importlib.util.spec_from_file_location('parent_export',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def row(pc,kind,a=0,**extra):return {'pc':pc,'file_offset':256+pc*4,'kind':kind,'A':a,'writes':[a] if kind in ('getglobal','loadk','move') else [],**extra}
def ir(rows,blocks=None):
    return {'root_function':{'path':'root','instructions':rows,'children':[],
        'blocks':[{'instruction_pcs':p} for p in (blocks or [[r['pc'] for r in rows]])]}}
def calls(name='parent',target='Fate_Shift_Start'):
    return [row(0,'getglobal',constant_lua=json.dumps(name)),row(1,'loadk',a=1,constant_lua=json.dumps(target)),row(2,'call_fixed',B=3,kills=[0,1,2])]
checks=0
def check(ok):
    global checks
    assert ok;checks+=1
for name in ('parent','require'):
    found,unknown=module.dependencies(ir(calls(name)));check(len(found)==1 and found[0]['module']=='Fate_Shift_Start' and found[0]['via']==name and not unknown)
found,unknown=module.dependencies(ir(calls(target='folder/Name.lua')));check(found[0]['module']=='folder/Name.lua')
found,unknown=module.dependencies(ir(calls(),[[0,1],[2]]));check(not found and len(unknown)==1)
rows=calls();rows[1]=row(1,'move',a=1,B=4);found,unknown=module.dependencies(ir(rows));check(not found and len(unknown)==1)
found,unknown=module.dependencies(ir(calls('my_parent')));check(not found and not unknown)
rows=calls();rows.insert(2,row(3,'getglobal',a=0,constant_lua='"something_else"'));found,unknown=module.dependencies(ir(rows));check(not found and len(unknown)==1)
rows=calls();rows[2]['B']=1;found,unknown=module.dependencies(ir(rows));check(not found and len(unknown)==1)
print(json.dumps({'ok':True,'checks':checks,'scope':'Exact literal parent/require inventory, no aliases/path normalization/cross-block inference'}))
