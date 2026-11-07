"""Evaluate only reconstructed top-level data declarations in an isolated Lua5.1 VM.
No native game binding executes. SL carriers retained verbatim; asset-ID names resolve
from installed symbol table or remain symbolic; engine getter references are inert.
This is a data-extraction validation, not original-engine runtime equivalence proof."""
from pathlib import Path
import json,sys,re,hashlib
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
sys.path.insert(0,str(ROOT/'tools/python-libs'))
from lupa.lua51 import LuaRuntime,lua_type
lua=LuaRuntime(register_eval=False,register_builtins=False)
sym=json.loads((ROOT/'work/v49-character-create/analysis/expanded-symbols.json').read_text())
for kind in ['ability','buff','simtype','fab','actor_state']:
 tab=lua.table_from({v.lower():int(k) for k,v in sym.get(kind,{}).items()})
 lua.globals()[kind.upper()+'_ID']=lua.eval('function(t,k) return function(n) return t[string.lower(n)] or (k..":"..n) end end')(tab,kind)
lua.execute('require=function(s) end; SL=function(t) return t end;GAME={is_content_package_active=function(...) return true end};PLAYER={};PlayerStartingInventory={items={}};standardLibrary={append_tables=function(...) local o={} for _,t in ipairs({...}) do for _,v in ipairs(t) do o[#o+1]=v end end return o end}')
# Inventory placeholders permit unrelated inventory definitions; do not publish them
# as actual source IDs. No PLAYER operation is called while loading declarations.
for i in range(1,100): lua.globals().PlayerStartingInventory['items'][i]='UNRESOLVED_STARTING_ITEM:'+str(i)
p=ROOT/'outputs/initial-corpus-drafts-v05/scripts/a7a3739dcf1830095983e123adc9bc20358aa2eedd53116bdf6798784beafec3'
t=(p/'whole-script.lua').read_text()
for name in sorted(set(re.findall(r'"([a-zA-Z][a-zA-Z_0-9]+)"',t))):
 if name.startswith(('get_','set_','is_','can_','add_','remove_')):
  lua.globals().PLAYER[name]=lua.eval('function(n) return function() error("unexpected PLAYER call:"..n) end end')(name)
status='complete'
try:lua.execute(t)
except Exception as e:status=str(e)
cd=lua.globals().character_data
def conv(x):
 if lua_type(x)=='table': return {str(k):conv(v) for k,v in x.items()}
 if lua_type(x)=='function': return '<closure>'
 return x
data={k:conv(v) for k,v in cd.items() if k.startswith('m_')}
out=Path(__file__).resolve().parent
(out/'character-data-tables.json').write_text(json.dumps(data,indent=2))
ir=json.loads((p/'ir.json').read_text())
published=['m_race_hashes','m_gender_hashes','m_char_gen_simtypes_lite','m_char_gen_simtypes','m_customization_presets','m_default_customization','m_skills_by_race','m_patrons_by_race','m_patron_buffs','m_gen_options','m_char_gen_fabs']
provenance={k:[{f:x[f] for f in ['pc','file_offset','name']} for x in ir['root_function']['instructions'] if x['kind']=='setglobal' and x.get('constant_lua')==json.dumps(k)] for k in published}
(out/'character-data-extraction.json').write_text(json.dumps({'input_id':751829,'input_sha256':ir['input_sha256'],'status':status,'source':str(p),'table_assignment_provenance':provenance,'limitations':['Static reconstruction rather than original source','DLC activity simulated enabled; not entitlement proof','SL localization carrier retained, not translated','Engine getter closures referenced but never called','Unresolved asset names retained symbolically','Starting inventory placeholders not actual items']},indent=2))
print('status',status,'tables',len(data))
