import re,struct
c=open(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe','rb').read()
S=[(0x401000,0xf60c00,0x400),(0x1362000,0x453800,0xf61000),(0x17b6000,0x1c2a00,0x13b4800)]
def o2v(o):
    for v,s,r in S:
        if r<=o<r+s:return o-r+v
def v2o(v):
    for va,s,r in S:
        if va<=v<va+s:return v-va+r
rd=c[0xf61000:0xf61000+0x453800]
for name in [b'.?AVRegion@BHG@@',b'.?AVEnvironmentProbeInstanceMgr@BHG@@']:
    i=c.find(name);td=o2v(i)-8
    P=struct.pack('<I',td)
    for m in re.finditer(re.escape(P),rd):
        col=o2v(0xf61000+m.start())-12
        if col%4:continue
        sig,off,cd=struct.unpack_from('<III',c,v2o(col))
        if sig!=0:continue
        for m2 in re.finditer(re.escape(struct.pack('<I',col)),rd):
            vt=o2v(0xf61000+m2.start())+4
            print(name.decode(),'vtable',hex(vt),'off',off,[hex(x) for x in struct.unpack_from('<14I',c,v2o(vt))])
