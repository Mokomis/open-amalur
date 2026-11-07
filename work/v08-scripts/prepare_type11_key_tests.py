"""Windows-only frozen-emitter fixtures for canonical type11 table keys."""
import argparse,hashlib,json,platform,sys
from pathlib import Path
assert platform.system()=='Windows'
root=Path.home()/'Documents/Opem Amalur'
parser=argparse.ArgumentParser();parser.add_argument('--carrier',required=True,type=Path)
args=parser.parse_args()
sys.path.insert(0,str(root/'src'))
from amalur_script import decode_instruction
from amalur_reconstruct import reconstruct
# Import the staged v08 adapter, never silently use src's previous adapter.
import importlib.util
adapter_path=Path(__file__).with_name('module_source_adapter.py')
spec=importlib.util.spec_from_file_location('type11_v08_adapter',adapter_path)
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
profile=json.loads((root/'outputs/native-script-profile.json').read_text())
out=root/'outputs/scene-v08/type11-key-tests';out.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def word(op,a=0,b=0,c=0):return (op<<25)|a|(b<<17)|(c<<8)
reports=[]
def generate(name,code,parameters,stack=4):
    owned=[]
    for instruction in code:
        owned.append(instruction)
        opcode=(instruction>>25)&127
        owned.extend([word(profile['inline_data_opcode'])]*profile['opcodes'][str(opcode)].get('inline_data_words',0))
    code=owned
    fn={'instructions':[decode_instruction(w,0x100+i*4,i) for i,w in enumerate(code)],
        'constants':[],'children':[],'parameter_count':parameters,'maximum_stack_size':stack,
        'upvalue_count':0,'vararg_flags':0}
    ir,source=reconstruct({'input_sha256':'0'*64,'chunk':{'root_function':fn}},profile)
    assert ir['root_function']['body_emittable'],ir['root_function']['unknowns']
    adapted,report=adapter.adapt_source(source)
    expected=0 if name=='method' else 1
    assert report['canonical_type11_key_guards_adapted']==expected,report
    assert report['self_key_guards_preserved']==(1 if name=='method' else 0),report
    (out/(name+'-original.lua')).write_text(source,encoding='utf-8')
    (out/(name+'-adapted.lua')).write_text(adapted,encoding='utf-8')
    reports.append({'name':name,**report})
    return 'local function '+name+'(...)\n'+adapted+'\nend\n'
text='-- Frozen v05 generated instructions; v08 canonical handle key guard only.\n'
for op in (10,11,12):text+=generate('read'+str(op),[word(op,a=2,b=0,c=1),word(9,a=2,b=2)],2)
for op in (16,18,20):text+=generate('write'+str(op),[word(op,a=0,b=1,c=2),word(9,b=1)],3)
text+=generate('method',[word(8,a=2,b=0,c=1),word(9,a=2,b=3)],2)
text+='''
local checks=0
local function check(ok) checks=checks+1;assert(ok,'type11 key check '..checks) end
local function rejected(fn,...) local ok,err=pcall(fn,...);check(not ok and type(err)=='string') end
local carrier=__amalur_uint64
local host=__amalur_type11_key_allowed
check(type(host)=='function')
local a=carrier.from_hex('00000001000004ab')
local same=carrier.from_hex('00000001000004AB')
local domain=carrier.from_hex('000000010000035b')
local low_highbit=carrier.from_hex('00000001800004ab')
local high=carrier.from_hex('80000001000004ab')
local maximum=carrier.from_hex('fffffffffffffffb')
check(rawequal(a,same))
check(host(a)==true and host(newproxy(true))==false)
check(host(nil)==false and host(a,a)==false)
local fake=newproxy(true);getmetatable(fake).__metatable='Amalur type-11 opaque carrier v1'
check(host(fake)==false)
local function other_realm()
'''
carrier_path=args.carrier
text+=carrier_path.read_text(encoding='utf-8-sig')
text+='''
end
local foreign=other_realm().from_hex('00000001000004ab')
check(host(foreign)==false)
local readers={read10,read11,read12};local writers={write16,write18,write20}
for _,write in ipairs(writers) do
  local t={}
  write(t,a,11);write(t,domain,12);write(t,high,13);write(t,maximum,14);write(t,low_highbit,15)
  for _,read in ipairs(readers) do
    check(read(t,same)==11);check(read(t,domain)==12);check(read(t,high)==13)
    check(read(t,maximum)==14);check(read(t,low_highbit)==15)
    check(read(t,carrier.from_hex('00000002000004ab'))==nil)
    rejected(read,t,fake);rejected(read,t,foreign)
    for _,bad in ipairs({false,0.5,1/0,{},function()end}) do rejected(read,t,bad) end
    rejected(read,t,nil);rejected(read,t,0/0)
  end
  write(t,same,21);check(t[a]==21)
  write(t,a,nil);check(t[same]==nil)
  write(t,'plain',31);write(t,-2147483648,32);write(t,2147483647,33)
  check(t.plain==31 and t[-2147483648]==32 and t[2147483647]==33)
  rejected(write,t,fake,1);rejected(write,t,foreign,1);rejected(write,t,nil,1)
  rejected(write,t,false,1);rejected(write,t,2147483648,1)
  rejected(write,setmetatable({},{__index={}}),a,1)
end
local t={};local fn=function()end;t.method=fn;t[a]=fn
local found,receiver=method(t,'method');check(found==fn and receiver==t)
rejected(method,t,a);rejected(method,t,1)
-- Changing the public carrier method cannot broaden the host's captured predicate.
local original_is=carrier.is;carrier.is=function()return true end
check(host(fake)==false and host(foreign)==false and host(a)==true)
rejected(write16,{},fake,1);write16(t,a,77);check(read12(t,same)==77)
carrier.is=original_is
-- Absence of the optional host helper fails closed for handles, preserving primitives.
__amalur_type11_key_allowed=nil
rejected(write16,{},a,1);local plain={};write16(plain,'a',9);check(read12(plain,'a')==9)
__amalur_type11_key_allowed=host
return checks
'''
(out/'type11-key-harness.lua').write_text(text,encoding='utf-8')
(out/'modules.tsv').write_text('Type11KeyHarness\ttype11-key-harness.lua\n',encoding='utf-8')
report={'scope':'Synthetic frozen-emitter table-key integration; no original game execution or allocation/iteration parity claim.',
        'native_evidence':['work/v08-native/vm_generic_table_get.json','work/v08-native/vm_generic_table_set.json'],
        'emitter_sha256':sha(root/'src/amalur_reconstruct.py'),'adapter_sha256':sha(adapter_path),
        'carrier_sha256':sha(carrier_path),'fixtures':reports,
        'files':{p.name:sha(p) for p in out.glob('*') if p.is_file() and p.name!='provenance.json'}}
(out/'provenance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'directory':str(out),'fixture_count':len(reports),'adapted_key_guards':sum(x['canonical_type11_key_guards_adapted'] for x in reports),'self_preserved':sum(x['self_key_guards_preserved'] for x in reports),'adapter_sha256':sha(adapter_path)}))
