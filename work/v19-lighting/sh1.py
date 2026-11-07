import json,re,os
idx=json.load(open('outputs/scene-v19/shader-index.json'));D='outputs/scene-v19/shaders/'
fw=sorted([k for k,v in idx.items() if 'g_forwardLightingbuffer' in v['cbuffers'] and v['type']=='ps'],key=lambda k:idx[k]['lines'])
print('forward ps',len(fw),[idx[k]['lines'] for k in fw[:6]])
t=open(D+fw[0]+'.asm',encoding='latin1').read()
# global buffer layout
m=re.search(r'// cbuffer g_globalbuffer.*?// \}',t,re.S);print(re.sub(r'\n//\s*\n','\n',m.group(0))[:3800] if m else 'noglobal')
m=re.search(r'// cbuffer g_forwardLightingbuffer.*?// \}',t,re.S);print(m.group(0)[:900])
m=re.search(r'// cbuffer g_dynamicbuffer.*?// \}',t,re.S);print(m.group(0)[:1000] if m else '')
print('RES',re.search(r'// Resource Bindings:.*?(?=\n//\n// \n|\n// Input)',t,re.S).group(0)[:1400])
print('---BODY',fw[0]);body=t[t.index('ps_'):];print(body[:7000])
