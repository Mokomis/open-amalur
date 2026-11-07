"""Windows-only generated-bytecode tests for the narrow function/nil EQ domain."""
import hashlib,json,platform,sys
from pathlib import Path
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur'
sys.path.insert(0,str(root/'src'))
from amalur_script import decode_instruction
from amalur_reconstruct import reconstruct
from module_source_adapter import adapt_source
profile=json.loads((root/'outputs/native-script-profile.json').read_text())
out=root/'outputs/scene-v07/equality-guard-tests';out.mkdir(parents=True,exist_ok=True)
def word(op,a=0,b=0,c=0):return (op<<25)|a|(b<<17)|(c<<8)
def generate(name,opcode,polarity):
    code=[word(opcode,a=polarity,b=0,c=1),(28<<25)|((65535+2)<<8),
          word(13,a=2,b=0),word(9,a=2,b=2),word(13,a=2,b=1),word(9,a=2,b=2)]
    fn={'instructions':[decode_instruction(w,0x100+i*4,i) for i,w in enumerate(code)],
        'constants':[],'children':[],'parameter_count':2,'maximum_stack_size':3,'upvalue_count':0,'vararg_flags':0}
    ir,source=reconstruct({'input_sha256':'0'*64,'chunk':{'root_function':fn}},profile)
    assert ir['root_function']['body_emittable'],ir['root_function']['unknowns']
    adapted,report=adapt_source(source)
    assert report['function_nil_equality_guards_adapted']==(1 if opcode==4 else 0),report
    (out/(name+'-original.lua')).write_text(source,encoding='utf-8')
    return 'local function '+name+'(...)\n'+adapted+'\nend\n'
text='-- Synthetic bytecode emitted by frozen v05; only v07 guards are adapted.\n'
for name,opcode,polarity in [('eq',4,1),('ne',4,0),('lt',50,1),('le',52,1)]:text+=generate(name,opcode,polarity)
text+='''
local f=function()end
local c=type -- Stock Lua C function; Amalur math.abs itself is a Lua wrapper.
for _,fn in ipairs({f,c}) do
  assert(eq(fn,nil)==false and eq(nil,fn)==false)
  assert(ne(fn,nil)==true and ne(nil,fn)==true)
  assert(not pcall(eq,fn,fn) and not pcall(ne,fn,fn))
  assert(not pcall(eq,fn,function()end))
  for _,v in ipairs({0,false,'x',{}}) do
    assert(not pcall(eq,fn,v) and not pcall(eq,v,fn))
  end
  assert(not pcall(lt,fn,nil) and not pcall(lt,nil,fn))
  assert(not pcall(le,fn,nil) and not pcall(le,nil,fn))
end
assert(eq(nil,nil)==true and ne(nil,nil)==false)
assert(eq(1,1)==true and eq(1,2)==false and eq(false,nil)==false)
assert(eq('a','a')==true and ne('a','b')==true)
assert(lt(1,2)==true and le(2,2)==true)
assert(not pcall(eq,{},nil) and not pcall(eq,nil,{}))
local token=__amalur_handles.from_words(0x19b,7813)
assert(not pcall(eq,token,nil) and not pcall(eq,nil,token))
assert(not pcall(eq,0.5,nil) and not pcall(eq,nil,0.5))
return 1
'''
(out/'equality-harness.lua').write_text(text,encoding='utf-8')
(out/'modules.tsv').write_text('EqualityHarness\tequality-harness.lua\n',encoding='utf-8')
report={'scope':'Synthetic generated-bytecode function/nil EQ domain; same-tag and other domains remain rejected.',
        'native_evidence':'branch-handlers.json: tag masks010af981/984, zero result010af995, tag mismatch jump010af99d/99f→010afabd',
        'emitter_sha256':hashlib.sha256((root/'src/amalur_reconstruct.py').read_bytes()).hexdigest(),
        'adapter_sha256':hashlib.sha256(Path(__file__).with_name('module_source_adapter.py').read_bytes()).hexdigest(),
        'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*') if p.is_file() and p.name!='provenance.json'}}
(out/'provenance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'directory':str(out),'files':len(report['files'])}))
