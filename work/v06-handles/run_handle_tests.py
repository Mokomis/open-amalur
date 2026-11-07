"""Windows Lua5.1 checks for exact marshaling, not engine behavior."""
import hashlib,json,platform,sys
from pathlib import Path
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur';sys.path.insert(0,str(root/'tools/python-libs'))
from lupa.lua51 import LuaRuntime,LUA_VERSION
assert tuple(LUA_VERSION)==(5,1)
here=Path(__file__).resolve().parent
carrier_path=root/'src/amalur_uint64.lua'
if not carrier_path.exists():carrier_path=root/'work/v05-parser/amalur_uint64.lua'
lua=LuaRuntime(unpack_returned_tuples=True,register_eval=False,register_builtins=False)
lua.execute("debug.sethook(function() error('handle fixture budget') end,'',100000); io=nil;os=nil;python=nil;dofile=nil;loadfile=nil;require=nil;debug=nil")
carrier_source=carrier_path.read_text();factory=lua.eval('function()\n'+carrier_source+'\nend')
module=lua.execute((here/'amalur_engine_handles.lua').read_text())
checks=lua.execute((here/'test_engine_handles.lua').read_text(),factory,module)
result={'scope':'Exact native type11 word/domain marshaling only; no game query, native callback or resource existence test.',
        'passed':len(checks),'checks':[checks[i] for i in range(1,len(checks)+1)],'native_behavior_claim':False,
        'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [carrier_path,here/'amalur_engine_handles.lua',here/'test_engine_handles.lua']}}
out=root/'outputs/engine-bindings-v06/handle-marshaling-validation.json';out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
