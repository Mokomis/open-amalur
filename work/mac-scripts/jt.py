import struct
c=open(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe','rb').read()
o=lambda v:v-0x401000+0x400
print(c[o(0xd42f90):o(0xd42fc0)].hex())
T=0xd43af8
for op in (0x3f,0x40,0x41,0x42,0x27):
    print(hex(op),hex(struct.unpack_from('<I',c,o(T)+4*(op-1))[0]),hex(struct.unpack_from('<I',c,o(T)+4*op)[0]))
