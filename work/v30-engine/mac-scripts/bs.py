import re,struct
c=open(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe','rb').read()
t=c[0x400:0x400+0xf60c00]
for name,pat in [('push560',b'\x68\x60\x05\x00\x00'),('push 0x460(fwd?)',b'\x68\x80\x00\x00\x00\x6a\x00')]:
    h=[hex(m.start()+0x401000) for m in re.finditer(re.escape(pat),t)]
    print(name,len(h),h[:20])
# jump-table dispatcher candidates: cmp reg,imm near 0x40..0xa0 followed by ja + jmp [reg*4+tbl]
for m in re.finditer(rb'\x0f\xb7[\x00-\xff]{1,3}[\x00-\xff]{0,12}\x3d[\x40-\xff]\x00\x00\x00\x0f\x87[\x00-\xff]{4}\xff\x24[\x80-\x8f]',t):
    print('switch16',hex(m.start()+0x401000),m.group().hex())
for m in re.finditer(rb'[\x83][\xf8-\xff][\x40-\x7f]\x0f\x87[\x00-\xff]{4}\xff\x24[\x80-\xbf]([\x00-\xff]{4})',t):
    a=m.start()+0x401000
    if 0xc00000<a<0xd80000:print('switch8',hex(a),hex(t[m.start()+2]),hex(struct.unpack('<I',m.group(1))[0]))
