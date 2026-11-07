import struct,sys
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"
b=None
for p in (root/"work/v19-inputs/initial_0.pak/luminance_shift.bxml",root/"work/v20-inputs/initial_0.pak/luminance_shift.bxml"):
    if p.exists():b=p.read_bytes();print(p,len(b));break
names={0xb7ce2a:'character_tint',0xdd0b0d:'environment_tint',0x31dbd9:'sky_tint',0x16242a8:'character_luminance',0x1a0ec77:'environment_luminance',0x9e7553:'sky_luminance',0xe292f8:'character_scale',0x10ecc7d:'environment_scale',0x4a20a1:'sky_scale',0xac9349:'character_max',0xd06184:'environment_max',0x2cced2:'sky_max',0x14401b0:'fog_distance_scale',0x1138f27:'fog_density_scale',0xd18944:'sky_speed_scale',0x182ff62:'bloom_exposure_scale',0x94fa56:'bloom_min_lum',0x9fe5b0:'bloom_max_lum',0x17d4686:'bloom_strength_scale'}
print(b[:64].hex());W=struct.unpack_from(f"<{len(b)//4}I",b)
print("words",len(W));print([hex(x) for x in W[:40]])
print("hash positions",sorted((i,names[v]) for i,v in enumerate(W) if v in names))
print("floats",[(i,round(struct.unpack_from('<f',b,i*4)[0],4)) for i in range(len(W)) if 1e-4<abs(struct.unpack_from('<f',b,i*4)[0])<1e4])
