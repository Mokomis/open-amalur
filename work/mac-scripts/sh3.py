import re,sys
D='outputs/scene-v19/shaders/'
for k in sys.argv[1:]:
    t=open(D+k+'.asm',encoding='latin1').read()
    c=re.findall(r'^//\s+(?:row_major )?(?:float\d?(?:x\d)?|int\d?|uint\d?|bool)\s+\w+(?:\[\d+\])?;\s+// Offset:\s+\d+',t,re.M)
    cb=[re.sub(r'\s+',' ',x[2:]) for x in c if not re.search(r'(hair|lt[A-Z]|wind|veggie|treeLeaf|snow|water|cycling|pulsing|fXAlpha|gameTime|terrain|normalBlend|PAD)',x)]
    print('#####',k);print(' | '.join(cb)[:1100])
    print('\n'.join(re.findall(r'^// (\S+?)(?:_F_\S*)?\s+(?:texture|cbuffer)\s.*?(t\d+|cb\d+)\s',t,re.M) and [a+' '+b for a,b in re.findall(r'^// (\S+?)(?:_F_\S*)?\s+(?:texture|cbuffer)\s.*?\b(t\d+|cb\d+)\s',t,re.M)]))
    b=t[re.search(r'^(ps|vs)_\d_\d',t,re.M).start():]
    b=re.sub(r'^dcl_(sampler|temps|globalFlags).*\n','',b,flags=re.M)
    print(b[:4200])
