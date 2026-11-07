import struct,glob,collections
def load(f):
    b=open(f,'rb').read();pl,fx=struct.unpack('<II',b[:8]);p=b[8:8+pl]
    return p,sorted({struct.unpack_from('<I',b,8+pl+i)[0] for i in range(0,fx,4)})
for f in ['work/v19-inputs/DATA_0.pak/524912.region_bxml','work/v19-inputs/patch_0.pak/524912.region_bxml']:
    p,fx=load(f);print(f,len(p),len(fx))
    print('root e0..100',[hex(x) for x in struct.unpack_from('<8I',p,0xe0)],struct.unpack_from('<8f',p,0xf8))
    ptr,n=struct.unpack_from('<II',p,0xe8);print('cube ptr',hex(ptr-8),n)
    print('tail fixups',[(hex(s),hex(struct.unpack_from('<I',p,s)[0]-8),struct.unpack_from('<I',p,s+4)[0]) for s in fx if s>=0x3900][:24])
    q=ptr-8
    print('first',p[q:q+0x48].hex())
    print('row20',p[q+0x30:q+0x60].hex())
    if n>1:
        e=(struct.unpack_from('<I',p,0xf0)[0]-8-q)/n;print('stride',e)
    print('after env',p[struct.unpack_from('<I',p,0xf0)[0]-8+0x570:][:0x80].hex())
s=collections.Counter()
for f in glob.glob('work/v19-inputs/DATA_0.pak/*.region_bxml')+glob.glob('work/v19-inputs/patch_0.pak/*.region_bxml'):
    try:
        p,_=load(f);ptr,n=struct.unpack_from('<II',p,0xe8);e=struct.unpack_from('<I',p,0xf0)[0]
        s[(n,(e-ptr)/n if n else 0)]+=1
    except Exception as ex:s['err']+=1
print(s.most_common(10))
import os
b=open('work/v19-inputs/initial_0.pak/1579973.koalighting','rb').read();print(struct.unpack_from('<14I',b,0))
