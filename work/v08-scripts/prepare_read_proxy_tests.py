"""Windows-only frozen-emitter fixtures for one approved READ fallback hop."""
import hashlib,importlib.util,json,platform,sys
from pathlib import Path
assert platform.system()=='Windows'
root=Path.home()/'Documents/Opem Amalur';sys.path.insert(0,str(root/'src'))
from amalur_script import decode_instruction
from amalur_reconstruct import reconstruct
adapter_path=Path(__file__).with_name('module_source_adapter.py')
spec=importlib.util.spec_from_file_location('read_proxy_adapter',adapter_path)
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
profile=json.loads((root/'outputs/native-script-profile.json').read_text())
out=root/'outputs/scene-v08/read-proxy-tests';out.mkdir(parents=True,exist_ok=True)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def word(op,a=0,b=0,c=0):return (op<<25)|a|(b<<17)|(c<<8)
reports=[]
def generate(name,code,parameters,category):
    owned=[]
    for instruction in code:
        owned.append(instruction);opcode=(instruction>>25)&127
        owned.extend([word(profile['inline_data_opcode'])]*profile['opcodes'][str(opcode)].get('inline_data_words',0))
    fn={'instructions':[decode_instruction(w,0x100+i*4,i) for i,w in enumerate(owned)],
        'constants':[{'type':'string','value':{'bytes_hex':b'value'.hex()}}],
        'children':[],'parameter_count':parameters,'maximum_stack_size':4,'upvalue_count':0,'vararg_flags':0}
    ir,source=reconstruct({'input_sha256':'0'*64,'chunk':{'root_function':fn}},profile)
    assert ir['root_function']['body_emittable'],ir['root_function']['unknowns']
    adapted,report=adapter.adapt_source(source)
    for key in ('proxy_read_field_guards_adapted','proxy_read_table_guards_adapted','write_table_guards_preserved','self_table_guards_preserved'):
        assert report[key]==(1 if key==category else 0),(name,key,report)
    if category in ('write_table_guards_preserved','self_table_guards_preserved'):
        assert 'if __type(__table) ~= "table" or not __field_table_allowed(__table) then' in adapted
        assert 'if __type(__table) ~= "table" or not __read_table_allowed(__table) then' not in adapted
    (out/(name+'-original.lua')).write_text(source,encoding='utf-8');(out/(name+'-adapted.lua')).write_text(adapted,encoding='utf-8')
    reports.append({'name':name,**report});return 'local function '+name+'(...)\n'+adapted+'\nend\n'
text='-- Frozen v05 instructions; v08 one-hop read admission, writes/SELF unchanged.\n'
text+=generate('field',[word(0,a=1,b=0,c=0),word(9,a=1,b=2)],1,'proxy_read_field_guards_adapted')
text+=generate('cached_field',[word(7,a=2,b=0),word(67,a=3,b=2,c=0),word(9,a=3,b=2)],1,'proxy_read_field_guards_adapted')
for op in (10,11,12):text+=generate('read'+str(op),[word(op,a=2,b=0,c=1),word(9,a=2,b=2)],2,'proxy_read_table_guards_adapted')
text+=generate('write_field',[word(15,a=0,b=0,c=1),word(9,b=1)],2,'write_table_guards_preserved')
text+=generate('write_cached_field',[word(7,a=0,b=0),word(68,a=0,b=0,c=1),word(9,b=1)],2,'write_table_guards_preserved')
text+=generate('write_table',[word(16,a=0,b=1,c=2),word(9,b=1)],3,'write_table_guards_preserved')
text+=generate('method',[word(8,a=2,b=0,c=1),word(9,a=2,b=3)],2,'self_table_guards_preserved')
text+='''
local checks=0
local function check(ok)checks=checks+1;assert(ok,'read proxy check '..checks)end
local function rejected(fn,...)local ok,err=pcall(fn,...);check(not ok and type(err)=='string' and string.find(err,'domain',1,true)~=nil)end
local host=__amalur_read_table_allowed;check(type(host)=='function')
local token=__amalur_uint64.from_hex('00000001000004ab')
local writes,executed=0,0
local fn=function()return 5 end
local internal={value=7,[-2147483648]=8,[2147483647]=9,[token]=10,method=fn}
local proxy=setmetatable({own=11},{__index=internal,__newindex=function()writes=writes+1 end})
local fields={field,cached_field};local readers={read10,read11,read12}
for _,read in ipairs(fields)do check(read(proxy)==7 and read(internal)==7)end
for _,read in ipairs(readers)do
  check(read(proxy,'value')==7 and read(proxy,'own')==11 and read(proxy,'missing')==nil)
  check(read(proxy,-2147483648)==8 and read(proxy,2147483647)==9 and read(proxy,token)==10)
  rejected(read,proxy,nil);rejected(read,proxy,false);rejected(read,proxy,0.5);rejected(read,proxy,{})
end
rejected(write_field,proxy,17);rejected(write_cached_field,proxy,17)
rejected(write_table,proxy,'value',17);rejected(write_table,proxy,'own',17);rejected(write_table,proxy,token,17)
check(writes==0 and internal.value==7 and proxy.own==11)
rejected(method,proxy,'method');local f,receiver=method(internal,'method');check(f==fn and receiver==internal)
local function bad_index()executed=executed+1;return 999 end
local forbidden={
  setmetatable({},{__index=bad_index}),
  setmetatable({},{__index=newproxy(true)}),
  setmetatable({},{__index=17}),
  setmetatable({},{__index=internal,__metatable='hidden'}),
  setmetatable({},{__index=internal,__metatable=false}),
  setmetatable({},{__index=bad_index,__metatable={__index=internal}}),
  setmetatable({},setmetatable({__index=internal},{__index=bad_index})),
  setmetatable({},{__index=setmetatable({},{__index=internal})}),
  setmetatable({},{__index=setmetatable({value=7},{__index=_G})})
}
local cycle={};setmetatable(cycle,{__index=cycle});forbidden[#forbidden+1]=cycle
local a,b={},{};setmetatable(a,{__index=b});setmetatable(b,{__index=a});forbidden[#forbidden+1]=a
for _,value in ipairs(forbidden)do
  for _,read in ipairs(fields)do rejected(read,value)end
  for _,read in ipairs(readers)do rejected(read,value,'value')end
  check(host(value)==false)
end
check(executed==0)
local registered=require('ReadGuardModule')
__read_guard_global=61
local via_registered=setmetatable({},{__index=registered,__newindex=function()writes=writes+1 end})
for _,read in ipairs(fields)do check(read(via_registered)==47 and read(registered)==47)end
for _,read in ipairs(readers)do check(read(via_registered,'value')==47 and read(via_registered,'__read_guard_global')==61)end
write_field(registered,53);check(field(registered)==53 and field(via_registered)==53)
rejected(write_field,via_registered,60);rejected(method,via_registered,'method');check(writes==0)
local registered_mt=getmetatable(registered);registered_mt.__newindex=bad_index
rejected(field,via_registered);check(executed==0);registered_mt.__newindex=nil
check(field(via_registered)==53)
local mt=getmetatable(proxy);mt.__index=bad_index;rejected(field,proxy);check(executed==0);mt.__index=internal
check(field(proxy)==7)
check(host(newproxy(true))==false and host(proxy,proxy)==false)
__amalur_read_table_allowed=nil
rejected(field,proxy);check(field(internal)==7 and field(registered)==53)
__amalur_read_table_allowed=host
check(field(proxy)==7)
return checks
'''
(out/'read-proxy-harness.lua').write_text(text,encoding='utf-8')
(out/'read-guard-module.lua').write_text("module('ReadGuardModule',package.seeall);value=47\n",encoding='utf-8')
(out/'modules.tsv').write_text('ReadGuardModule\tread-guard-module.lua\nReadProxyHarness\tread-proxy-harness.lua\n',encoding='utf-8')
report={'scope':'Synthetic frozen-emitter one-hop table read integration; no function metamethod admission, writes/SELF unchanged.',
        'emitter_sha256':sha(root/'src/amalur_reconstruct.py'),'adapter_sha256':sha(adapter_path),'fixtures':reports,
        'totals':{key:sum(r[key] for r in reports) for key in ('proxy_read_field_guards_adapted','proxy_read_table_guards_adapted','write_table_guards_preserved','self_table_guards_preserved')},
        'files':{p.name:sha(p) for p in out.glob('*') if p.is_file() and p.name!='provenance.json'}}
(out/'provenance.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'directory':str(out),'fixture_count':len(reports),'totals':report['totals'],'adapter_sha256':report['adapter_sha256']}))
