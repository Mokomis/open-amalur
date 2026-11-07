import json,re
idx=json.load(open('outputs/scene-v19/shader-index.json'));D='outputs/scene-v19/shaders/'
rows=[]
for k,v in idx.items():
    if 'g_globalbuffer' not in v['cbuffers']:continue
    t=open(D+k+'.asm',encoding='latin1').read()
    m=re.search(r'g_globalbuffer\s+cbuffer\s+NA\s+NA\s+cb(\d+)',t)
    if not m:continue
    c=m.group(1)
    if re.search(r'\bcb%s\[1\]\.'%c,t):
        rows.append((v['type'],v['lines'],k,bool(re.search('depth',t,re.I)),len(re.findall(r'\bexp\b',t))))
rows.sort()
print(len(rows),[r for r in rows if r[0]=='vs'][:6],[r for r in rows if r[0]=='ps'][:8])
vs=[r for r in rows if r[0]=='vs']
if vs:
    t=open(D+vs[0][2]+'.asm',encoding='latin1').read();b=t[t.index('vs_'):]
    for l in b.split('\n'):
        if re.search(r'cb\d\[1\]\.|dcl_output|dp4 o|mov o|mul o|mad o',l):print(l[:90])
