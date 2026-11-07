"""Submit REA pseudo-code/xref requests and print compact results. Args: d:ADDR (decompile), x:ADDR (xrefs), c:ADDR (callers), e:ADDR (callees)."""
import sys,json,time,re,os
from pathlib import Path
r=Path.home()/'Documents/Opem Amalur';q=r/'work/scene-v19c-requests';o=r/'outputs/scene-v19/rea-session-live3'
M=int(os.environ.get('MAXCHARS','5000'))
T={'a':('procedure_assembly','procedure'),'d':('procedure_pseudo_code','procedure'),'x':('xrefs','address'),'c':('procedure_callers','procedure'),'e':('procedure_callees','procedure')}
jobs=[]
for a in sys.argv[1:]:
    k,v=a.split(':',1);tool,arg=T[k];jobs.append((f'{k}_{v}',tool,{arg:v}))
n=len(list(q.glob('*.json')))
for l,t,g in jobs:
    if (o/(l+'.json')).exists():continue
    n+=1;(q/f"{n:04d}-{l}.json").write_text(json.dumps(dict(label=l,tool=t,arguments=g)),encoding='utf-8')
end=time.time()+float(os.environ.get('WAIT','560'))
for l,t,g in jobs:
    p=o/(l+'.json')
    while not p.exists() and time.time()<end:time.sleep(.3)
    print('#####',l)
    if not p.exists():print('TIMEOUT');continue
    for _ in range(30):
        try:d=json.loads(p.read_text(encoding='utf-8'));break
        except Exception:time.sleep(.3)
    J=d.get('structuredContent')
    if J is None:
        s='\n'.join(c.get('text','') for c in d.get('content',[]))
        try:J=json.loads(s)
        except Exception:J=s
    N=J.get('normalized_result',J) if isinstance(J,dict) else J
    if isinstance(N,dict):
        for k in ('pseudo_code','pseudocode','code','text','source','decompiled'):
            if isinstance(N.get(k),str):N=N[k];break
    s=N if isinstance(N,str) else json.dumps(N,separators=(',',':'))
    s=re.sub(r'\n\s*\n+','\n',s.replace('\r',''))
    s=re.sub(r'^\s*(undefined\d?|int|uint|float|bool|char|byte)\s+\*?\*?[\w\[\]\s]+;\n','',s,flags=re.M) if os.environ.get('NODECL','1')=='1' else s
    print(s[:M])
