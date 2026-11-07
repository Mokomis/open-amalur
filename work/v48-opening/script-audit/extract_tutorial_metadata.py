"""Read the original tutorial-data declarations in isolated Lua5.1.
Only module loading, literal localization IDs, and literal input-action symbols
are substituted to retain structured metadata. No callback or engine service runs.
"""
from pathlib import Path
import sys,json
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent
sys.path[:0]=[str(P/'tools/python-libs'),str(P/'work/v08-scripts')]
from lupa.lua51 import LuaRuntime,lua_type
from module_source_adapter import adapt_source
l=LuaRuntime(unpack_returned_tuples=True,max_memory=64*1024*1024)
l.execute(r'''
__amalur_module_table_allowed=function(t)
 local mt=getmetatable(t)
 return type(t)=="table" and type(mt)=="table" and mt.__index==_G and t._NAME=="tutorial_data"
end
SL=function(t)return {literal_localization_ids=t}end
INPUT_ACTION_KEY=function(n)return "INPUT_ACTION_KEY:"..n end
package.preload.tutorial_win=function() tutorial_win={};return tutorial_win end
debug.sethook(function()error("data extraction instruction budget")end,"",8000000)
''')
text=(Q/'evidence/tutorial_data/whole-script.lua').read_text()
source,receipt=adapt_source(text)
l.execute(source)
m=l.globals().tutorial_data
def conv(x,seen=None):
 if lua_type(x)=='function':return {'source_callback':'unexecuted'}
 if lua_type(x)=='table':
  pairs=list(x.items())
  if pairs and all(isinstance(k,(int,float)) and k>=1 and int(k)==k for k,_ in pairs) and set(k for k,_ in pairs)==set(range(1,len(pairs)+1)):
   return [conv(x[i]) for i in range(1,len(pairs)+1)]
  return {str(k):conv(v) for k,v in pairs}
 return x
rows=conv(m.m_tutorial_table)
if isinstance(rows,dict):rows=[rows[k] for k in sorted(rows,key=int)]
out={'scope':'Original recovered literal tutorial declarations; localization ID pairs retained, input symbols retained, all source callbacks unexecuted. Not translated UI or gameplay proof.','script_sha256':'93b362f2db7f6464f05a6ae9a6ab17193eeb6a0a291aa128e8d2d4521d279cab','count':len(rows),'adapter':receipt,'entries':rows}
(Q/'tutorial-data-literals.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
ids={17524338,26339831,23936604,49968583,25608663,61835887,40879367}
print(json.dumps({'count':len(rows),'selected':[r for r in rows if r.get('id_hash') in ids]},indent=2))
