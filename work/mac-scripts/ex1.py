import re,struct
c=open(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe','rb').read()
e=struct.unpack_from('<I',c,0x3c)[0];n=struct.unpack_from('<H',c,e+6)[0];op=struct.unpack_from('<H',c,e+20)[0];ib=struct.unpack_from('<I',c,e+52)[0]
S=[]
for i in range(n):
    o=e+24+op+40*i;nm=c[o:o+8].rstrip(b'\0');vs,va,rs,ra=struct.unpack_from('<4I',c,o+8);S.append((nm,va+ib,vs,ra,rs));print(nm,hex(va+ib),hex(vs),hex(ra),hex(rs))
def v2o(v):
    for nm,va,vs,ra,rs in S:
        if va<=v<va+rs:return v-va+ra
def o2v(o):
    for nm,va,vs,ra,rs in S:
        if ra<=o<ra+rs:return o-ra+va
print('DXBC',len(re.findall(b'DXBC',c)),[hex(o2v(m.start())) for m in list(re.finditer(b'DXBC',c))[:6]])
print('RDEF',len(re.findall(b'RDEF',c)))
o=v2o(0x19525a4);w=struct.unpack_from('<24I',c,o);print('table',[hex(x) for x in w])
s=lambda v:c[v2o(v):c.index(b'\0',v2o(v))] if v2o(v) else None
# dump table start: walk back to find bounds
base=0x19525a4
for k in range(-6,10):
    q=struct.unpack_from('<I',c,v2o(base+4*k))[0];print(hex(base+4*k),hex(q),s(q)[:40] if v2o(q) and q<0x1900000 else '')
f=c[v2o(0x171f810)-0x40:v2o(0x171f810)+0x60];print(f)
d=c[v2o(0x1708e55)-0x80:v2o(0x1708e55)+0x100];print(d)
