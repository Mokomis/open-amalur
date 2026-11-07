import itertools
c=open('work/v19-inputs/initial_0.pak/1525613.dds','rb').read();print(len(c),c[32:44].hex())
D=c[38:];assert len(D)==16384
best=[]
for perm in itertools.permutations(range(4),3):
    err=0
    for z in range(16):
        for y in range(16):
            for x in range(16):
                t=D[(z*256+y*16+x)*4:(z*256+y*16+x)*4+4]
                for a,e in zip(perm,(x,y,z)):err+=abs(t[a]-e*17)
    best.append((err/(4096*3),perm))
best.sort();print('mean abs error by channel order',best[:3])
_,P=best[0]
t=lambda x,y,z:[D[(z*256+y*16+x)*4+a] for a in P]
print('black',t(0,0,0),'white',t(15,15,15),'mid',t(8,8,8),'red',t(15,0,0),'green',t(0,15,0),'blue',t(0,0,15),'alpha',D[3],D[(4095*4)+3])
