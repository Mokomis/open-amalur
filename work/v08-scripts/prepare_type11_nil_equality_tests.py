"""Windows-only frozen-emitter fixtures for canonical type11 versus nil EQ."""
import argparse, hashlib, importlib.util, json, platform, sys
from pathlib import Path
assert platform.system() == 'Windows'
parser = argparse.ArgumentParser()
parser.add_argument('--carrier', required=True, type=Path)
args = parser.parse_args()
root = Path.home() / 'Documents/Opem Amalur'
sys.path.insert(0, str(root / 'src'))
from amalur_script import decode_instruction
from amalur_reconstruct import reconstruct
adapter_path = Path(__file__).with_name('module_source_adapter.py')
spec = importlib.util.spec_from_file_location('nil_eq_v08_adapter', adapter_path)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
profile = json.loads((root / 'outputs/native-script-profile.json').read_text())
out = root / 'outputs/scene-v08/type11-nil-equality-tests'
out.mkdir(parents=True, exist_ok=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def word(op, a=0, b=0, c=0): return (op << 25) | a | (b << 17) | (c << 8)
reports = []
def generate(name, opcode, polarity):
    # EQ branches over its following JMP; branch target returns true/false.
    code = [word(opcode, a=polarity, b=0, c=1), (28 << 25) | ((65535+2) << 8),
            word(13, a=2, b=0), word(9, a=2, b=2),
            word(13, a=2, b=1), word(9, a=2, b=2)]
    fn = {'instructions': [decode_instruction(w, 0x100+i*4, i) for i,w in enumerate(code)],
          'constants': [], 'children': [], 'parameter_count': 2,
          'maximum_stack_size': 3, 'upvalue_count': 0, 'vararg_flags': 0}
    ir, source = reconstruct({'input_sha256': '0'*64, 'chunk': {'root_function': fn}}, profile)
    assert ir['root_function']['body_emittable'], ir['root_function']['unknowns']
    adapted, report = adapter.adapt_source(source)
    assert report['canonical_type11_nil_equality_guards_adapted'] == (1 if opcode == 4 else 0), report
    (out / (name+'-original.lua')).write_text(source, encoding='utf-8')
    (out / (name+'-adapted.lua')).write_text(adapted, encoding='utf-8')
    reports.append({'name': name, **report})
    return 'local function '+name+'(...)\n'+adapted+'\nend\n'
text = '-- Frozen v05 synthetic bytecode; narrow v08 carrier/nil comparison guard.\n'
for name, opcode, polarity in [('eq',4,1),('ne',4,0),('lt',50,1),('le',52,1)]:
    text += generate(name,opcode,polarity)
text += '''
local checks=0
local function check(ok) checks=checks+1;assert(ok,'type11 nil equality check '..checks) end
local function rejected(fn,...) local ok,err=pcall(fn,...);check(not ok and type(err)=='string') end
local carrier=__amalur_uint64
local host=__amalur_type11_key_allowed
check(type(host)=='function')
local function other_realm()
'''
text += args.carrier.read_text(encoding='utf-8-sig')
text += '''
end
local foreign=other_realm().from_hex('00000001000002fb')
local fake=newproxy(true)
local fake_mt=getmetatable(fake)
fake_mt.__eq=function()error('arbitrary userdata equality invoked')end
fake_mt.__metatable='Amalur type-11 opaque carrier v1'
local handles={
  carrier.from_hex('000000000000000b'),
  carrier.from_hex('00000001000002fb'),
  carrier.from_hex('80000001800002fb'),
  carrier.from_hex('fffffffffffffffb')
}
for _,h in ipairs(handles) do
  check(eq(h,nil)==false);check(eq(nil,h)==false)
  check(ne(h,nil)==true);check(ne(nil,h)==true)
  -- No same-tag or other heterogeneous equality extension.
  rejected(eq,h,h);rejected(ne,h,h)
  rejected(eq,h,handles[2]);rejected(ne,h,handles[2])
  for _,v in ipairs({0,false,'x',{},function()end,fake,foreign}) do
    rejected(eq,h,v);rejected(eq,v,h);rejected(ne,h,v);rejected(ne,v,h)
  end
  for _,fn in ipairs({lt,le}) do rejected(fn,h,nil);rejected(fn,nil,h) end
end
for _,bad in ipairs({fake,foreign,newproxy(true),{},setmetatable({},{__eq=function()error('table equality invoked')end}),0.5,2147483648,1/0,0/0}) do
  rejected(eq,bad,nil);rejected(eq,nil,bad);rejected(ne,bad,nil);rejected(ne,nil,bad)
end
-- Existing primitive and function/nil cases are retained.
check(eq(nil,nil)==true);check(ne(nil,nil)==false)
check(eq(1,1)==true);check(eq(1,2)==false);check(eq(false,nil)==false)
check(eq('a','a')==true);check(ne('a','b')==true)
check(lt(1,2)==true);check(le(2,2)==true)
for _,fn in ipairs({function()end,type}) do
  check(eq(fn,nil)==false);check(eq(nil,fn)==false)
  check(ne(fn,nil)==true);check(ne(nil,fn)==true)
  rejected(eq,fn,fn);rejected(ne,fn,fn)
end
-- A forged public membership predicate cannot widen the captured host predicate.
local original_is=carrier.is;carrier.is=function()return true end
check(eq(handles[2],nil)==false);rejected(eq,fake,nil);rejected(eq,foreign,nil)
carrier.is=original_is
-- Optional helper absence fails closed while primitive/function behavior remains.
__amalur_type11_key_allowed=nil
rejected(eq,handles[2],nil);rejected(eq,nil,handles[2])
rejected(ne,handles[2],nil);rejected(ne,nil,handles[2])
check(eq(nil,nil)==true);check(eq(function()end,nil)==false)
__amalur_type11_key_allowed=host
check(ne(handles[2],nil)==true)
return checks
'''
(out/'type11-nil-equality-harness.lua').write_text(text,encoding='utf-8')
(out/'modules.tsv').write_text('Type11NilEqualityHarness\ttype11-nil-equality-harness.lua\n',encoding='utf-8')
report={'scope':'Canonical realm type11 versus nil EQ/NE only; same-tag, arbitrary userdata, table equality and ordered comparisons unchanged.',
        'native_evidence':'work/branch-handlers.json EQ010af926: tag masks010af981/984, zero result010af995, mismatch010af99d/99f jumps010afabd before same-tag dispatch.',
        'emitter_sha256':sha(root/'src/amalur_reconstruct.py'),'adapter_sha256':sha(adapter_path),
        'carrier_sha256':sha(args.carrier),'fixtures':reports,
        'files':{p.name:sha(p) for p in out.glob('*') if p.is_file() and p.name!='provenance.json'}}
(out/'provenance.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'directory':str(out),'fixture_count':len(reports),'canonical_type11_nil_equality_guards':sum(x['canonical_type11_nil_equality_guards_adapted'] for x in reports),'adapter_sha256':sha(adapter_path)}))
