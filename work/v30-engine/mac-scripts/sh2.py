import json,re,collections
idx=json.load(open('outputs/scene-v19/shader-index.json'));D='outputs/scene-v19/shaders/'
def res(k):
    t=open(D+k+'.asm',encoding='latin1').read();return re.findall(r'^// (g_\w+?|[A-Za-z_]\w*)_texture\s+texture|^// (\w+)\s+texture',t,re.M),t
print('== post/special (no material buffer)')
for k,v in sorted(idx.items(),key=lambda kv:kv[1]['lines']):
    if v['type']!='ps' or 'g_materialbuffer' in v['cbuffers']:continue
    t=open(D+k+'.asm',encoding='latin1').read()
    tx=[re.sub(r'_F_.*','',a) for a in re.findall(r'^// (\S+)\s+texture\s',t,re.M)]
    vs=[x for x in v['vars'] if x not in idx and not re.match('(hair|lt|gameTime|tree|wind|veggie|snow|water|cycling|pulsing|fXAlpha|terrain|normalBlend|sunlightFog|backlight|ambient|world$|worldVector|worldView|object|dissolve|cameraD|cameraP|depthT|invDepth|texelS)',x)]
    print(k,v['lines'],v['cbuffers'],'TEX',tx,'VARS',[x for x in vs if x not in('fogColor','worldToFogConstants','sunLightColor','sunLightColor_PAD0','sunLightDirection','sunLightDirection_PAD0','skyLightColor','shadowColor','environmentTint','globalTintColor','luminanceFactors','luminanceTint','luminanceShiftId')][:14])
print('== texture names across material PS')
c=collections.Counter()
for k,v in idx.items():
    if v['type']!='ps':continue
    t=open(D+k+'.asm',encoding='latin1').read()
    for a in re.findall(r'^// (\S+)\s+texture\s',t,re.M):c[re.sub(r'_F_.*','',a)]+=1
print(c.most_common(60))
print('== global const usage')
u=collections.Counter()
for k,v in idx.items():
    if v['type']!='ps':continue
    t=open(D+k+'.asm',encoding='latin1').read()
    m=re.search(r'g_globalbuffer\s+cbuffer\s+NA\s+NA\s+cb(\d+)',t)
    if not m:continue
    cb=m.group(1)
    for r in set(re.findall(r'\bcb%s\[(\d+)\]'%cb,t)):u[int(r)]+=1
print(sorted(u.items())[:30])
