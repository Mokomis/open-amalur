import struct,glob,os,json,collections,hashlib
exec(open('work/v19-lighting/scan5.py',encoding='utf-8').read().split('# Solve:')[0])
anchor=[('fog_start',0x280),('fog_density',0x290),('post_bloom_scale',0x2a0),('post_bloom_cutoff',0x2b0),('bloom_exposure_level',0x330),('bloom_strength',0x360)]
pairs=[]
for f,(r,_,_) in recs.items():
    sc=[]
    for n,d in XML.items():
        s=sum(1 for ki,k in enumerate(K) for nm,off in anchor if (k,nm) in d and abs(struct.unpack_from('<f',r,off+4*ki)[0]-d[(k,nm)])<1e-5*(abs(d[(k,nm)])+1))
        sc.append((s,n))
    t=[n for s,n in sc if s==24]
    if t:pairs.append((f,t))
print('pairs',len(pairs),'unique-preset',sum(1 for _,t in pairs if len(t)==1))
votes=collections.defaultdict(collections.Counter);tot=collections.Counter()
nfl=0x570//4
for f,t in pairs:
    if len(t)!=1:continue
    r=recs[f][0];v=struct.unpack('<%df'%nfl,r);d=XML[t[0]]
    for key,x in d.items():
        if not isinstance(x,float):continue
        tot[key]+=1
        for i,y in enumerate(v):
            if abs(y-x)<=1e-5*(abs(x)+1e-3):votes[key][4*i]+=1
res={}
for key,c in sorted(votes.items(),key=lambda kv:(kv[1].most_common(1)[0][0] if kv[1] else 9999,str(kv[0]))):
    top=c.most_common(3)
    if key[0] in('Noon',''):print(key,tot[key],[(hex(o),n) for o,n in top])
    res[str(key)]=[(o,n) for o,n in c.most_common(4)]
json.dump(res,open('outputs/scene-v19/field-solve-2.json','w'),indent=0)
a,b=[recs[f] for f in recs if f.endswith('524912.region_bxml')]
print('shop DATA vs patch record same',a[0]==b[0],'whole payload same',a[1]==b[1],len(a[1]),len(b[1]))
if a[0]!=b[0]:
    print('diff offs',[hex(i) for i in range(0,0x570,4) if a[0][i:i+4]!=b[0][i:i+4]][:60])
pv=[f for f in recs if f.endswith('524912.region_bxml')]
print(pv)
for name in ('lighting_int_dal_gorhartinn_region.koalighting','dlc1_lighting_int_dal_gorhartinn_region_shadows.koalighting'):
    A=XML[name];print(name,'dir',[A.get(('','dir.%d'%i)) for i in range(3)],'flags',A[('','flags')],'cc',A[('Noon','color_correction_texture')][-70:],'cube',A[('Noon','ambient_cube')][-50:],'char',A[('Noon','character_ambient_cube')][-40:])
A=XML['lighting_int_dal_gorhartinn_region.koalighting'];B=XML['dlc1_lighting_int_dal_gorhartinn_region_shadows.koalighting']
print('diff fields',[(k,A.get(k),B.get(k)) for k in set(A)|set(B) if A.get(k)!=B.get(k)][:25])
for rr in (a,):
    print('rec 0x3d0',rr[0][0x3d0:0x3e0].hex(),'0x420',rr[0][0x420:0x440].hex())
