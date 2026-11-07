"""Print a saved REA result's normalized payload. Usage: rv.py label [regex] [maxchars]"""
import sys,json,re
from pathlib import Path
o=Path.home()/'Documents/Opem Amalur/outputs/scene-v19/rea-session-live'
d=json.loads((o/(sys.argv[1]+'.json')).read_text(encoding='utf-8'))
def get(d):
    if 'structuredContent' in d:return d['structuredContent']
    t='\n'.join(c.get('text','') for c in d.get('content',[]))
    try:return json.loads(t)
    except Exception:return t
J=get(d)
N=J.get('normalized_result',J) if isinstance(J,dict) else J
rx=re.compile(sys.argv[2],re.I) if len(sys.argv)>2 and sys.argv[2] else None
M=int(sys.argv[3]) if len(sys.argv)>3 else 8000
if isinstance(N,list):
    rows=[(r.get('address','')+' '+str(r.get('value',r.get('name',r)))) if isinstance(r,dict) else str(r) for r in N]
    if rx:rows=[r for r in rows if rx.search(r)]
    print(len(rows));print('\n'.join(rows)[:M])
else:print((json.dumps(N,indent=0) if not isinstance(N,str) else N)[:M])
