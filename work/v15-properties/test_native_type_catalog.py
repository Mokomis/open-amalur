import struct,unittest
from native_type_catalog import index_batch,member_bytes,CatalogError,CatalogLimits

def fixture():
 return struct.pack('<5I',2,230417,56,226948,64)+bytes(120)

class CatalogTests(unittest.TestCase):
 def test_exact_spans(self):
  data=fixture();d=index_batch(data)
  self.assertEqual(d['count'],2)
  self.assertEqual(d['members'][230417]['offset'],20)
  self.assertEqual(d['members'][226948]['offset'],76)
  self.assertEqual(len(member_bytes(data,d['members'][226948])),64)

 def test_corrupt_directories_and_trailing_data(self):
  for offset,value in [(0,0),(0,0xffffffff),(8,0xffffffff),(12,230417),(16,7)]:
   b=bytearray(fixture());struct.pack_into('<I',b,offset,value)
   with self.subTest(offset=offset,value=value),self.assertRaises(CatalogError):index_batch(bytes(b))
  with self.assertRaises(CatalogError):index_batch(fixture()+b'x')
  with self.assertRaises(CatalogError):index_batch(fixture(),CatalogLimits(max_bytes=128))

 def test_every_truncated_directory_or_payload(self):
  data=fixture()
  for end in range(len(data)):
   with self.subTest(end=end),self.assertRaises(CatalogError):index_batch(data[:end])

if __name__=='__main__':unittest.main()
