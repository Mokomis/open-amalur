"""Windows unit checks for explicit preview identity selection and dependency retention."""
import copy,importlib.util,json,platform
from pathlib import Path
assert platform.system()=='Windows'
path=Path(__file__).with_name('export_scene_modules_v08.py')
spec=importlib.util.spec_from_file_location('selection_export',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
checks=0
def check(ok):
    global checks
    assert ok;checks+=1
def reject(fn,*args):
    try:fn(*args)
    except ValueError:check(True)
    else:raise AssertionError('Expected rejection')
a='a'*64;b='b'*64
matches=[{'name':'example','file':'base.lua_bxml','sha256':a},
         {'name':'example','file':'patch.lua_bxml','sha256':b}]
original=copy.deepcopy(matches)
chosen,ambiguity,receipt=module.select_candidate('example',matches,{})
check(chosen is None and receipt is None)
check(ambiguity['resolution']=='unresolved' and ambiguity['candidates']==original)
selected=module.parse_selections(['example='+a.upper()])
check(selected=={'example':a})
chosen,ambiguity,receipt=module.select_candidate('example',matches,selected)
check(chosen==matches[0])
check(ambiguity['resolution']=='explicit_preview_selection' and ambiguity['selected_input_sha256']==a)
check(ambiguity['candidates']==original and matches==original)
check(receipt['unselected_input_sha256']==[b] and receipt['candidate_identities']==[a,b])
check('not native archive precedence' in receipt['reason'])
chosen,_,_=module.select_candidate('example',list(reversed(matches)),selected)
check(chosen['sha256']==a and chosen['file']=='base.lua_bxml')
chosen,ambiguity,receipt=module.select_candidate('example',[matches[0]],{})
check(chosen==matches[0] and ambiguity is None and receipt is None)
chosen,ambiguity,_=module.select_candidate('example',[matches[0],dict(matches[0],file='same-bytes.lua_bxml')],{})
check(chosen['sha256']==a and ambiguity is None)
reject(module.select_candidate,'example',matches,{'example':'c'*64})
reject(module.select_candidate,'Example',[],{'Example':a})
for value in ['', 'example', 'example='+a+'=x', 'example='+a[:63], 'example='+'z'*64,
              '../example='+a, 'example/name='+a, 'example:name='+a, 'a\tb='+a, '='+a,
              ('x'*256)+'='+a]:reject(module.parse_selections,[value])
reject(module.parse_selections,['example='+a,'example='+a])
reject(module.parse_selections,['example='+a,'example='+b])
reject(module.parse_selections,['ParentUtils='+a])
reject(module.parse_selections,['name'+str(i)+'='+a for i in range(257)])
check(module.parse_selections(['ParentUtils='+module.PARENT_INPUT_SHA])=={'ParentUtils':module.PARENT_INPUT_SHA})
# A selected record follows the same dependency pass as every other identity.
rows=[{'pc':0,'file_offset':0,'kind':'getglobal','A':0,'writes':[0],'constant_lua':'"require"'},
      {'pc':1,'file_offset':4,'kind':'loadk','A':1,'writes':[1],'constant_lua':'"message_box_win"'},
      {'pc':2,'file_offset':8,'kind':'call_fixed','A':0,'B':2,'kills':[0,1]}]
ir={'root_function':{'path':'root','instructions':rows,'children':[],'blocks':[{'instruction_pcs':[0,1,2]}]}}
found,unknown=module.dependencies(ir)
check(len(found)==1 and found[0]['module']=='message_box_win' and found[0]['via']=='require' and not unknown)
print(json.dumps({'ok':True,'checks':checks,'scope':'Explicit exact identity selection, ambiguity preservation, input immutability, pinned ParentUtils and unchanged dependency discovery'}))
