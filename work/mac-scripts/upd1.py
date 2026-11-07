import re
p='work/v19-lighting/decode_scene_lighting.py';s=open(p,encoding='utf-8').read()
s=s.replace('status = "native_confirmed" if name.endswith("_cube_index") else "hypothesis"\n                rows[key] = field(blob.u32(at + 4 * index), at + 4 * index, status)','rows[key] = field(blob.u32(at + 4 * index), at + 4 * index, "native_confirmed")')
s=s.replace('ENV_UNMAPPED = ((0x000, 0x240), (0x43C, 0x440))','# FUN_00ccb310 does not read the first span from the record.\nENV_UNMAPPED = ((0x000, 0x240),)')
s=s.replace('direction = field([clean(x) for x in blob.floats(base + 0x430, 3)], base + 0x430, "asset_verified")','direction = field([clean(x) for x in blob.floats(base + 0x430, 3)], base + 0x430, "asset_verified")\n    flags = field(blob.u32(base + 0x43C), base + 0x43C, "native_confirmed", native_note="FUN_00ccb310 copies only bit 0")')
s=s.replace('"directional_light_direction": direction, "unmapped_spans"','"directional_light_direction": direction, "flags": flags, "unmapped_spans"')
s=s.replace('"sky_asset_id": field(blob.u32(ROOT_SKY_ID), ROOT_SKY_ID, "hypothesis")','"sky_asset_id": field(blob.u32(ROOT_SKY_ID), ROOT_SKY_ID, "native_confirmed")')
s=s.replace('SPACE_REGION_KEY = 0x48\n','SPACE_REGION_ID = 0x34\nSPACE_REGION_KEY = 0x48\n')
s=s.replace('"region_key": field(blob.payload[SPACE_REGION_KEY:SPACE_REGION_KEY + 8].hex(), SPACE_REGION_KEY, "asset_verified"),\n        "lights"','"region_asset_id": field(blob.u32(SPACE_REGION_ID), SPACE_REGION_ID, "native_confirmed"),\n        "region_key": field(blob.payload[SPACE_REGION_KEY:SPACE_REGION_KEY + 8].hex(), SPACE_REGION_KEY, "asset_verified"),\n        "lights"')
s=s.replace('# Field names map to the renderer stage that consumes them; see lighting-provenance.json.\n','''# Runtime snapshot offsets produced by FUN_00ccb310 then FUN_00c8a160.
SNAPSHOT_OFFSETS = {
    "fog_color": 0x00, "shadow_color": 0x10, "directional_light_color": 0x20,
    "environment_tint": 0x30, "particle_tint": 0x40, "sky_light_color": 0x50,
    "post_contrast": 0x60, "fog_start": 0x6C, "fog_density": 0x70, "shadow_opacity": 0x74,
    "directional_light_intensity": 0x78, "post_bloom_scale": 0x7C, "post_bloom_cutoff": 0x80,
    "post_brightness": 0x84, "post_focal_distance": 0x88, "post_focal_radius": 0x8C,
    "post_motion_blur": 0x90, "bloom_exposure_level": 0x94, "bloom_min_luminance": 0x98,
    "bloom_max_luminance": 0x9C, "bloom_strength": 0xA0, "dof_near_fuzzy": 0xA4,
    "dof_near_sharp": 0xA8, "dof_far_fuzzy": 0xAC, "dof_far_sharp": 0xB0, "dof_max_fuzzy": 0xB4,
    "edge_motion_blur": 0xB8, "directional_light_direction": 0xBC, "flags": 0xC8,
}
''')
open(p,'w',encoding='utf-8').write(s)
p='work/v19-lighting/lighting_model.py';s=open(p,encoding='utf-8').read()
s=s.replace('"""shader_confirmed: factor is min(1, 2^-(a*z+b)). How a and b derive from fog_start/fog_density is unresolved."""','"""shader_confirmed: factor is min(1, 2^-(a*z+b)); fog_constants gives a and b."""')
s+='''

def fog_constants(fog_start, fog_density, density_scale=1.0, distance_scale=1.0, shift_weight=0.0):
    """native_confirmed: FUN_00c8a880 and FUN_00cd6680. Globals only apply through shift_weight."""
    density = density_scale * fog_density * shift_weight + (1.0 - shift_weight) * fog_density
    distance = distance_scale * 500000.0 * shift_weight + (1.0 - shift_weight) * 500000.0
    return density / distance, fog_start


def sun_constants(rgb, hdr_intensity, directional_intensity, direction):
    """native_confirmed: FUN_00cd6680 packs rgb*hdr*intensity and the negated direction."""
    scale = hdr_intensity * directional_intensity
    return [c * scale for c in rgb], [-d for d in direction]
'''
open(p,'w',encoding='utf-8').write(s)
p='work/v19-lighting/test_lighting.py';s=open(p,encoding='utf-8').read()
s=s.replace("self.assertEqual(s['region_key']['value'],r['region_key']['value']);","self.assertEqual(s['region_key']['value'],r['region_key']['value']);self.assertEqual(s['region_asset_id']['value'],524912);")
s=s.replace("    def test_region_weight(self)","    def test_fog_constants(self):self.assertEqual(M.fog_constants(-.1,70),(70/500000,-.1))\n    def test_sun(self):self.assertEqual(M.sun_constants([1,2,3],2,.5,[0,0,-1])[0],[1,2,3]);self.assertEqual(M.sun_constants([1,1,1],1,1,[0,0,-1])[1],[-0,-0,1])\n    def test_region_weight(self)")
open(p,'w',encoding='utf-8').write(s)
import sys,hashlib
sys.path.insert(0,'work/v19-lighting')
import decode_scene_lighting as D
for a in('DATA_0.pak','patch_0.pak'):
    r=D.decode_region(open(f'work/v19-inputs/{a}/524912.region_bxml','rb').read())
    print(a,[c['pixels_sha256'][:8] for c in r['ambient_cubes']],'flags',r['environment']['flags']['value'])
    b=open(f'work/v19-inputs/{a}/524912.region_bxml','rb').read();p0=b[8:]
    print(' face0 first texels',p0[r['ambient_cubes'][0]['face_texel_offsets'][0]:][:16].hex())
import glob,collections
d=diff=0;c=collections.Counter()
for f in glob.glob('work/v19-inputs/patch_0.pak/*.region_bxml'):
    g=f.replace('patch_0','DATA_0')
    if not os.path.exists(g) if 'os' in dir() else False:continue
