import struct
b=open('work/scene-inputs-v07/DATA_0.pak/524912.region_bxml','rb').read();pl,fx=struct.unpack('<II',b[:8]);p=b[8:8+pl]
fxs=set(struct.unpack_from('<I',b,8+pl+i)[0] for i in range(0,fx,4))
print('root words');
for o in range(0,0x90,4):
    w=struct.unpack_from('<I',p,o)[0];print(hex(o),hex(w),'PTR->'+hex(w-8) if o in fxs else '',round(struct.unpack_from('<f',p,o)[0],3))
for s,e in [(0x33c4,0x3934)]:
    for o in range(s,e,16):
        r=struct.unpack_from('<4f',p,o);print(hex(o-s),' '.join('%.5g'%x for x in r),'  '+p[o:o+16].hex() if o-s>=0x420 or o-s<0x20 else '', 'P' if any(o+i in fxs for i in (0,4,8,12)) else '')
print('after',p[0x3934:0x39c0].hex())
