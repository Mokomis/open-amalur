import struct
b=open('work/v19-inputs/initial_0.pak/luminance_shift.bxml','rb').read()
n=struct.unpack_from('<I',b,0x10)[0];print('n',n,struct.unpack_from('<8I',b,0))
ent=struct.unpack_from('<%dI'%n,b,0x20);h=struct.unpack_from('<%dI'%n,b,0x20+4*n)
p=0x20+8*n;m,z=struct.unpack_from('<II',b,p);p+=8;print('strings',m,z)
S=[]
for i in range(m):
    l=struct.unpack_from('<I',b,p)[0];p+=4;S.append(b[p:p+l].decode('latin1'));p+=l
print(S,'left',len(b)-p,b[p:])
names={0xb7ce2a:'character_tint',0xdd0b0d:'environment_tint',0x31dbd9:'sky_tint',0x16242a8:'character_luminance',0x1a0ec77:'environment_luminance',0x9e7553:'sky_luminance',0xe292f8:'character_scale',0x10ecc7d:'environment_scale',0x4a20a1:'sky_scale',0xac9349:'character_max',0xd06184:'environment_max',0x2cced2:'sky_max',0x14401b0:'fog_distance_scale',0x1138f27:'fog_density_scale',0xd18944:'sky_speed_scale',0x182ff62:'bloom_exposure_scale',0x94fa56:'bloom_min_lum',0x9fe5b0:'bloom_max_lum',0x17d4686:'bloom_strength_scale'}
for e,k in zip(ent,h):
    idx=(e>>12)&0xffff
    print(hex(e),hex(k),names.get(k,'?'),S[idx] if idx<len(S) else idx)
