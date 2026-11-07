import sys,struct
sys.path.insert(0,'tools/python-libs')
import capstone
c=open(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe','rb').read()
o=lambda v:v-0x401000+0x400
T=0xd43af8
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
for op in (0x42,):
    a=struct.unpack_from('<I',c,o(T)+4*op)[0];print(hex(op),hex(a))
    for i in md.disasm(c[o(a):o(a)+0x40],a):print(hex(i.address),i.mnemonic,i.op_str)
# xrefs to merge shader setup object: search code calling 0xa03... via constant 0x40-size cbuffer
