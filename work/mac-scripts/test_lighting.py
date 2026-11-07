import glob,hashlib,struct,sys,unittest
sys.path.insert(0,'work/v19-lighting')
import decode_scene_lighting as D
import lighting_model as M

def synthetic_region():
    payload=bytearray(0x120+0x30+6*256+D.ENV_RECORD_BYTES)
    cube=0x120;pixels=cube+0x30;env=pixels+6*256
    fix=[D.ROOT_CUBES,D.ROOT_ENV]
    struct.pack_into('<II',payload,D.ROOT_CUBES,cube+8,1);struct.pack_into('<II',payload,D.ROOT_ENV,env+8,1)
    for f in range(6):
        struct.pack_into('<II',payload,cube+8*f,pixels+256*f+8,64);fix.append(cube+8*f)
    struct.pack_into('<8f',payload,D.ROOT_DAY_DIVISION,21,6,9,18,4,8,17,20)
    struct.pack_into('<f',payload,env+0x288,12.5)
    struct.pack_into('<4f',payload,env+0x400,.1,.2,.3,2)
    struct.pack_into('<3f',payload,env+0x430,0,0,-1)
    struct.pack_into('<I',payload,env+0x558,0)
    return struct.pack('<II',len(payload),4*len(fix))+bytes(payload)+struct.pack('<%dI'%len(fix),*fix)

class Decoder(unittest.TestCase):
    def test_synthetic_key_order_and_offsets(self):
        r=D.decode_region(synthetic_region());e=r['environment']['time_keyed']
        self.assertEqual(e['fog_start']['Noon']['value'],12.5)
        self.assertEqual(e['directional_light_color']['Noon']['value']['intensity'],2.0)
        self.assertEqual(r['day_division_hours']['value']['Midnight'],{'start':21.0,'end':4.0})
        self.assertEqual(len(r['ambient_cubes']),1)
    def test_rejects_truncation(self):
        with self.assertRaises(D.DecodeError):D.decode_region(synthetic_region()[:-1])
    def test_rejects_unregistered_pointer(self):
        b=bytearray(synthetic_region());pl,fx=struct.unpack_from('<II',b);b[8+pl:8+pl+4]=struct.pack('<I',0)
        with self.assertRaises(D.DecodeError):D.decode_region(bytes(b))
    def test_corpus_shop_region(self):
        f='work/v19-inputs/DATA_0.pak/524912.region_bxml';r=D.decode_region(open(f,'rb').read())
        self.assertEqual(r['region_key']['value'],'8f028bbe0c91181c');self.assertEqual(r['sky_asset_id']['value'],325844)
        self.assertEqual(len(r['ambient_cubes']),8)
        s=D.decode_space_lights(open('work/scene-inputs-v07/DATA_0.pak/524859.space_bxml','rb').read())
        self.assertEqual(s['region_key']['value'],r['region_key']['value']);self.assertEqual(len(s['lights']),36)
class Model(unittest.TestCase):
    def test_attenuation_endpoints(self):
        c,a,b=M.point_light_constants([1,1,1],1,.5,100,500)
        self.assertEqual(c,[.5,.5,.5]);self.assertAlmostEqual(M.point_attenuation(100,a,b),1);self.assertAlmostEqual(M.point_attenuation(500,a,b),0);self.assertAlmostEqual(M.point_attenuation(300,a,b),.5)
    def test_degenerate_range_uses_zero_start(self):
        _,a,b=M.point_light_constants([1,1,1],1,1,500,500);self.assertAlmostEqual(M.point_attenuation(250,a,b),.5)
    def test_key_blend(self):self.assertAlmostEqual(M.lerp_key([0,0,2,4],2,3,.5),3)
    def test_fog_full_near(self):self.assertEqual(M.fog_blend([1,1,1],[0,0,0],1,0,0),[1,1,1])
    def test_region_weight(self):self.assertAlmostEqual(M.region_blend_weight(500,1000),.5);self.assertEqual(M.region_blend_weight(2000,1000),0)
if __name__=='__main__':unittest.main(verbosity=1)
