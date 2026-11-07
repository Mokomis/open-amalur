import unittest,struct
from collision_set import parse,export_scene,CollisionError
def sample():
 b=bytearray(132);struct.pack_into('<6I',b,0,104,20,24,0,24,1);struct.pack_into('<iiII',b,24,0,0,40,1);struct.pack_into('<5I',b,40,0,60,3,96,1);struct.pack_into('<9f',b,60,0,0,0,1,0,0,0,1,0);struct.pack_into('<4I',b,96,0,1,2,20);struct.pack_into('<5I',b,112,0,8,24,36,44);return b
class Tests(unittest.TestCase):
 def test_exact_sample(self):
  x=parse(sample());self.assertEqual(len(x['groups'][0]['meshes'][0]['vertices']),3);out=export_scene(x,100);self.assertEqual(len(out),144);self.assertEqual(struct.unpack_from('<f',out,72)[0],100)
 def test_all_truncations(self):
  b=sample()
  for n in range(len(b)):
   with self.subTest(n=n),self.assertRaises(CollisionError):parse(b[:n])
 def test_bad_fields(self):
  for off,val in [(0,100),(4,19),(12,1),(16,0),(20,1025),(32,0xfffffff0),(36,257),(44,64),(48,500001),(52,100),(56,500001),(96,3),(112,4),(116,0)]:
   b=sample();struct.pack_into('<I',b,off,val)
   with self.subTest(off=off),self.assertRaises(CollisionError):parse(b)
 def test_nonfinite_and_large_positions(self):
  for v in [float('nan'),float('inf'),float('-inf'),10001.]:
   b=sample();struct.pack_into('<f',b,60,v)
   with self.subTest(v=v),self.assertRaises(CollisionError):parse(b)
 def test_extra_data(self):
  with self.assertRaises(CollisionError):parse(sample()+b'\0')
 def test_scale_must_be_explicit(self):
  with self.assertRaises(CollisionError):export_scene(parse(sample()),1)
if __name__=='__main__':unittest.main()
