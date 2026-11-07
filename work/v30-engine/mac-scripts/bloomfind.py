import json,re
idx=json.load(open('outputs/scene-v19/shader-index.json'));D='outputs/scene-v19/shaders/'
for k,v in idx.items():
    if v['type']!='ps' or v['lines']>70:continue
    t=open(D+k+'.asm',encoding='latin1').read()
    if re.search(r'0\.2126|0\.299',t) and 'g_materialbuffer' not in v['cbuffers'] and re.search(r'\bdiv\b|\bmul_sat\b|mad_sat|add_sat',t):
        print(k,v['lines'],v['cbuffers'],re.findall(r'^// (\S+?)(?:_F_\S*)?\s+texture\s',t,re.M))
