import sys,struct,collections
sys.path.insert(0,'tools/python-libs')
import capstone
c=open(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe','rb').read()
t=c[0x400:0x400+0xf60c00]
want={0x4fc:0,0x500:1,0x504:2,0x508:3,0x50c:4,0x510:5,0x4e0:6,0x4f0:7}
hits=collections.defaultdict(set)
for d in want:
    p=struct.pack('<I',d);i=0
    while True:
        i=t.find(p,i)
        if i<0:break
        if 0xa00000<i+0x401000<0x1100000:hits[(i+0x401000)//0x400].add(d)
        i+=1
for k,v in sorted(hits.items(),key=lambda kv:-len(kv[1]))[:10]:print(hex(k*0x400),sorted(hex(x) for x in v))
