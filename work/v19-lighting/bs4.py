import struct,re
c=open(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe','rb').read()
t=c[0x400:0x400+0xf60c00]
A=struct.pack('<I',0x128);B=struct.pack('<I',0x12c);C=struct.pack('<I',0x114)
h=[]
for m in re.finditer(re.escape(A),t):
    i=m.start();w=t[max(0,i-400):i+400]
    if B in w and C in w:h.append(i+0x401000)
print([hex(x) for x in h][:30])
r=[x for x in h if 0xc00000<x<0xd80000];print('range',[hex(x) for x in r])
