"""Submit REA requests to the v19 worker and print compact text results. Usage: rea_client.py <json-lines on stdin: label tool args>; MAXCHARS env."""
import sys,json,time,os
from pathlib import Path
r=Path.home()/'Documents/Opem Amalur';q=r/'work/scene-v19-requests';o=r/'outputs/scene-v19/rea-session-live'
M=int(os.environ.get('MAXCHARS','6000'))
jobs=[json.loads(l) for l in sys.stdin if l.strip()]
n=len(list(q.glob('*.json')))
for j in jobs:
    n+=1;(q/f"{n:04d}-{j['label']}.json").write_text(json.dumps(j),encoding='utf-8')
end=time.time()+float(os.environ.get('WAIT','500'))
def text(d):
    if isinstance(d,dict) and 'content' in d:
        return '\n'.join(c.get('text','') for c in d['content'])
    return json.dumps(d)
for j in jobs:
    p=o/(j['label']+'.json')
    while not p.exists() and time.time()<end: time.sleep(.5)
    print('#####',j['label'])
    if not p.exists():print('TIMEOUT');continue
    time.sleep(.1)
    for _ in range(20):
        try:d=json.loads(p.read_text(encoding='utf-8'));break
        except Exception:time.sleep(.3)
    t=text(d)
    try:
        J=json.loads(t)
        if isinstance(J,dict):
            for k in ('pseudo_code','pseudocode','code','text','result','results','matches','strings','procedures'):
                if k in J:
                    t=J[k] if isinstance(J[k],str) else json.dumps(J[k]);break
    except Exception:pass
    t=t.replace('\r','')
    while '\n\n' in t:t=t.replace('\n\n','\n')
    print(t[:M])
