"""Compare the explicit-field adapter with the recovered accessor bodies.
No engine/game execution, installation or user-state I/O.
"""
from pathlib import Path
import sys,json
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'tools/python-libs'))
from lupa.lua51 import LuaRuntime
l=LuaRuntime(unpack_returned_tuples=True,max_memory=32*1024*1024);g=l.globals()
g.A=l.execute((Q/'opening_state_accessors.lua').read_text())
g.original_get=l.execute((Q/'evidence/ModuleVariableStorage/functions/function_0_3.lua').read_text())
g.original_set=l.execute((Q/'evidence/ModuleVariableStorage/functions/function_0_2.lua').read_text())
l.execute(r'''
warnings={}
function warn(s)warnings[#warnings+1]=s end
WARN_LUA=warn
get_error_internal=function()return "fixture source" end
-- Deterministic diagnostic branch only; no engine service is represented here.
debug.getinfo=function()return nil end
native={current_state={flag=false,count=0,label="room1"}}
adapted={module_state={flag=false,count=0,label="room1"}}
before_mt={__index=_G};setmetatable(adapted,before_mt)
handle=A.install(adapted,warn)
function set_original(k,v)m_table_to_set_to=native;m_var_to_set=k;return original_set(v)end
function get_original(k)m_table_to_get_from=native;m_var_to_get=k;return original_get()end
''')
checks=0
def check(x,msg):
 global checks
 checks+=1;assert x,msg
check(l.eval('getmetatable(adapted)==before_mt'),'seeall metatable unchanged')
check(l.eval('adapted.module_state==nil and adapted.internal_module_state==true'),'native storage ownership markers')
for field,v in [('flag',True),('count',25),('label','room1b')]:
 g.set_original(field,v);g.adapted['set_'+field](v)
 check(g.get_original(field)==g.adapted['get_'+field](),'same-type original/adapter writes')
for field,v in [('flag',1),('count',False),('label',7)]:
 before=g.get_original(field);n=len(g.warnings);g.set_original(field,v);g.adapted['set_'+field](v)
 check(g.get_original(field)==before and g.adapted['get_'+field]()==before,'type-change rejects and retains old value')
 check(len(g.warnings)==n+2,'both implementations warn once')
check(g.get_original('unknown') is None,'original missing getter returns nil')
check(g.adapted.get_unknown is None,'adapter unknown accessor remains missing')
check(l.eval('adapted.getters.get_flag=="flag" and adapted.setters.set_flag=="flag"'),'source accessor maps retained')
snap=g.handle.snapshot();g.adapted.set_flag(False);check(g.handle.restore(snap) is True,'typed snapshot restores')
check(g.adapted.get_flag() is True,'restored original state')
l.execute('bad=handle.snapshot();bad.count=false')
r=g.handle.restore(g.bad);check(isinstance(r,tuple) and r[0] is False,'bad restore rejected')
check(g.adapted.get_flag() is True and g.adapted.get_count()==25,'bad restore did not partly mutate')
l.execute('bad=handle.snapshot();bad.extra=1');r=g.handle.restore(g.bad);check(isinstance(r,tuple) and r[0] is False,'unknown serialized field rejected')
check(l.eval('A.install(adapted,warn)==handle'),'repeat install idempotent')
l.execute('explicit={module_state={flag=false},get_flag=function()return "explicit"end};A.install(explicit,warn)')
check(g.explicit.get_flag()=='explicit','explicit source function has original raw-field precedence')
l.execute('unsupported={module_state={flag=false,object={}}};unsupported_ok=pcall(A.install,unsupported,warn)')
check(g.unsupported_ok is False,'unsupported table state rejected explicitly')
check(l.eval('unsupported.module_state~=nil and unsupported.current_state==nil and unsupported.get_flag==nil'),'unsupported initialization leaves module untouched')
out={'passed':True,'checks':checks,'scope':'Recovered original getters/setters versus explicit-field adapter; primitive opening subset, diagnostics recorded; no native game-equivalence or save-format claim','host_metatable_unchanged':True}
(Q/'state-accessor-fixture-results.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
