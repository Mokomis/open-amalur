import struct,math
import xml.etree.ElementTree as ET
b=open('work/scene-inputs-v07/DATA_0.pak/524912.region_bxml','rb').read();pl,fx=struct.unpack('<II',b[:8]);p=b[8:8+pl]
t=ET.parse('work/v19-inputs/initial_0.pak/lighting_int_dok_interior.koalighting').getroot().find('DataObject')
d=[float(x) for x in t.find("value[@name='directional_light_direction']").text.split()];print('name',t.attrib['name'],'dir',d,'flags',t.find("value[@name='flags']").text)
base=None
nd=struct.pack('<3f',*d);i=-1
while True:
    i=p.find(nd,i+1)
    if i<0:break
    print('dir at payload',hex(i))
    base=i-0x2f0
print('base',hex(base))
S=t.find("value[@name='settings']");K=['Midnight','Dawn','Noon','Dusk']
print('keys xml',[k.attrib['name'] for k in S])
rows={}
for ki,k in enumerate(S):
    for v in k:
        n=v.attrib['name'];ty=v.attrib['type']
        if ty=='float':rows[(k.attrib['name'],n)]=float(v.text)
        elif ty.endswith('HdrColorRgb'):
            for c in v:rows[(k.attrib['name'],n+'.'+c.attrib['name'])]=float(c.text)
        elif ty=='float4':
            for j,x in enumerate(v.text.split()):rows[(k.attrib['name'],n+'.%d'%j)]=float(x)
            print('float4',n,v.text)
rec=p[base:base+0x314]
vals=struct.unpack('<%df'%(0x314//4),rec)
loc={}
for key,x in rows.items():
    m=[hex(4*i) for i,y in enumerate(vals) if abs(y-x)<=abs(x)*1e-5+1e-9]
    loc[key]=m
for n in sorted({k[1] for k in rows}):
    print(n,[ (K2,(rows[(K2,n)],loc[(K2,n)][:6])) for K2 in ('Noon',) if (K2,n) in rows])
print('tail',rec[0x2f0:0x314].hex())
print('before',p[base-0x20:base].hex())
for i,w in enumerate(struct.unpack('<%dI'%(0x60//4),rec[:0x60])):pass
# Who points at base (fixup stored value == base+8)?
fxs=[struct.unpack_from('<I',b,8+pl+i)[0] for i in range(0,fx,4)]
print('ptrs to base',[hex(s) for s in fxs if struct.unpack_from('<I',p,s)[0]==base+8])
print('all targets near',sorted({hex(struct.unpack_from('<I',p,s)[0]-8) for s in fxs if base-0x400<struct.unpack_from('<I',p,s)[0]-8<base+0x800}))
