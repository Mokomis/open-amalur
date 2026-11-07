import json,re,sys
from pathlib import Path
o=Path.home()/'Documents/Opem Amalur/outputs/scene-v19/rea-session-live3'
for a in sys.argv[1:]:
    d=json.loads((o/f'd_{a}.json').read_text(encoding='utf-8'))
    J=d.get('structuredContent') or json.loads('\n'.join(c.get('text','') for c in d['content']))
    N=J.get('normalized_result',J)
    for k in ('pseudo_code','pseudocode','code','text','source','decompiled'):
        if isinstance(N,dict) and isinstance(N.get(k),str):N=N[k];break
    s=N if isinstance(N,str) else json.dumps(N)
    name=re.search(r'\b(FUN_\w+|\w+)\(',s)
    print(a,name.group(1) if name else '',len(s),'has128',bool(re.search(r'\+ 0x128\)|\+ 0x12c\)|\+ 300\)',s)),'pow/log',bool(re.search(r'0x3e59|0\.2126|brightness',s)))
