import sys
sys.path.insert(0,'tools/python-libs')
import capstone
c=open(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe','rb').read()
o=lambda v:v-0x401000+0x400
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
for a,n in [(0xd43737,0x30)]:
    for i in md.disasm(c[o(a):o(a)+n],a):print(hex(i.address),i.mnemonic,i.op_str)
