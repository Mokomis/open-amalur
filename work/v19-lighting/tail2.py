import json,sys,re
from pathlib import Path
o=Path.home()/'Documents/Opem Amalur/outputs/scene-v19/rea-session-live2'
d=json.loads((o/(sys.argv[1]+'.json')).read_text(encoding='utf-8'))
J=d.get('structuredContent') or json.loads('\n'.join(c.get('text','') for c in d['content']))
N=J.get('normalized_result',J)
for k in ('pseudo_code','pseudocode','code','text','source','decompiled'):
    if isinstance(N,dict) and isinstance(N.get(k),str):N=N[k];break
s=re.sub(r'\n\s*\n+','\n',N.replace('\r',''));s=re.sub(r'^\s*(undefined\d?|int|uint|float|bool|char|byte)\s+\*?\*?[\w\[\]\s]+;\n','',s,flags=re.M)
a=int(sys.argv[2]);print(len(s));print(s[a:a+int(sys.argv[3])])
