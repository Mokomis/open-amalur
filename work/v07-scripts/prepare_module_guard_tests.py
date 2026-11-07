"""Windows generated-bytecode guard integration cases for the module host."""
import hashlib,json,platform,sys
from pathlib import Path
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur'
sys.path.insert(0,str(root/'src'))
from amalur_script import decode_instruction
from amalur_reconstruct import reconstruct
from module_source_adapter import adapt_source
profile=json.loads((root/'outputs/native-script-profile.json').read_text())
out=root/'outputs/scene-v07/module-guard-tests';out.mkdir(parents=True,exist_ok=True)
def word(op,a=0,b=0,c=0):return (op<<25)|a|(b<<17)|(c<<8)
def generate(code,params):
    fn={'instructions':[decode_instruction(w,0x100+i*4,i) for i,w in enumerate(code)],
        'constants':[{'type':'string','value':{'bytes_hex':b'value'.hex()}}],
        'children':[],'parameter_count':params,'maximum_stack_size':2,'upvalue_count':0,'vararg_flags':0}
    ir,source=reconstruct({'input_sha256':'0'*64,'chunk':{'root_function':fn}},profile)
    assert ir['root_function']['body_emittable'],ir['root_function']['unknowns']
    return source,adapt_source(source)[0]
reader_original,reader=generate([word(0,a=1),word(70),word(70),word(9,a=1,b=2)],1)
writer_original,writer=generate([word(15,a=0,b=0,c=1),word(9,b=1)],2)
text='''-- Synthetic instructions emitted by the unchanged v0.5 reconstructor.
-- Exercises only the v0.7 registered-module table guard extension.
local function read(...)
'''+reader+'''
end
local function write(...)
'''+writer+'''
end
local m=require('GuardModule')
assert(read(m)==7)
write(m,11); assert(m.value==11 and read(m)==11)
local plain={value=23}; assert(read(plain)==23);write(plain,29);assert(plain.value==29)
assert(not pcall(read,setmetatable({value=1},{__index=_G})))
assert(not pcall(write,setmetatable({},{__index=_G}),1))
local mt=getmetatable(m);mt.__index=function()return 99 end
assert(not pcall(read,m));assert(not pcall(write,m,1))
mt.__index=_G;assert(read(m)==11)
mt.__newindex=function()error('unadmitted mutation')end
assert(not pcall(write,m,1));mt.__newindex=nil
write(m,13);assert(read(m)==13)
assert(getmetatable(m)==mt and mt.__index==_G)
return 9
'''
(out/'guard-harness.lua').write_text(text,encoding='utf-8')
(out/'guard-module.lua').write_text("module('GuardModule',package.seeall);value=7\n",encoding='utf-8')
(out/'modules.tsv').write_text('GuardModule\tguard-module.lua\nGuardHarness\tguard-harness.lua\n',encoding='utf-8')
(out/'reader-original.lua').write_text(reader_original,encoding='utf-8')
(out/'writer-original.lua').write_text(writer_original,encoding='utf-8')
report={'scope':'Synthetic generated-code module field/table guard integration; not original native execution.',
        'generated_by_sha256':hashlib.sha256((root/'src/amalur_reconstruct.py').read_bytes()).hexdigest(),
        'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*') if p.is_file()}}
(out/'provenance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'directory':str(out),'fixtures':len(report['source_sha256'])}))
