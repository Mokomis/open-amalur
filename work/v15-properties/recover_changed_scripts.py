"""Use the existing native-profile recovery pipeline on two new patch inputs only."""
from pathlib import Path
import json,sys,hashlib
r=Path.home()/'Documents/Opem Amalur';sys.path[:0]=[str(r/'src'),str(r/'tools/python-libs')]
from amalur_script import parse_file
from amalur_reconstruct import reconstruct
from lupa.lua51 import LuaRuntime,LUA_VERSION
assert tuple(LUA_VERSION)==(5,1)
profile=json.loads((r/'outputs/native-script-profile.json').read_text());out=r/'outputs/scene-v15/changed-script-drafts';out.mkdir(exist_ok=True)
lua=LuaRuntime(register_eval=False,register_builtins=False,unpack_returned_tuples=True);compile_only=lua.eval('function(s) local f,e=loadstring(s);return f~=nil,e end');rows=[]
for path in sorted((r/'work/v15-properties/changed-script-inputs').glob('*.lua_bxml')):
 parsed=parse_file(path);ir,text=reconstruct(parsed,profile);directory=out/parsed['input_sha256'];directory.mkdir(exist_ok=True)
 source=directory/'whole-script.lua'
 if source.exists() and source.read_text()!=text:raise ValueError('Preserve differing recovery draft')
 source.write_text(text,encoding='utf-8');(directory/'ir.json').write_text(json.dumps(ir,separators=(',',':')),encoding='utf-8')
 compiled,error=compile_only(text)
 row=dict(script_id=int(path.stem),input_sha256=parsed['input_sha256'],source_sha256=hashlib.sha256(text.encode()).hexdigest(),summary=ir['summary'],lua51_compiled=bool(compiled),compile_error=error,runtime_executed=False,existing_module_replaced=False,output=str(source));rows.append(row)
 if not compiled:raise ValueError(f'Lua draft compilation failed: {error}')
report=dict(status='New patch variants isolated and reconstructed with existing native profile',scripts=rows,scope='Guarded source recovery and Lua5.1 compilation only; unresolved bodies remain explicit. No module deployment or game behavior validation.')
(r/'outputs/scene-v15/changed-script-recovery.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
