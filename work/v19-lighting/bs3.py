import struct
c=open(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe','rb').read()
o=lambda v:v-0x401000+0x400
s=c[o(0xd41000):o(0xd41400)]
for d in (0x4fc,0x500,0x510):
    i=s.find(struct.pack('<I',d));print(hex(d),hex(0xd41000+i) if i>=0 else None)
