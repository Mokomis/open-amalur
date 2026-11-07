"""Windows-only synthetic KEEN/BC boundary and independent pixel checks."""
import platform,struct,unittest
assert platform.system()=='Windows'
from keen_texture import parse,decode,decode_blocks,color_block,bc3_block

def header(fmt=1,w=4,h=4,levels=1):
    b=bytearray(38);struct.pack_into('<IHHII',b,0,123,w,h,0,0);b[16:20]=b'KEEN';struct.pack_into('<HH',b,20,w,h)
    b[24:29]=b'\x01\0\x01\0\x01';b[29]=fmt;struct.pack_into('<H',b,35,levels);b[37]=1;return bytes(b)
def colors(c0=0xf800,c1=0x001f,indices=None):
    indices=indices or [i%4 for i in range(16)]
    return struct.pack('<HHI',c0,c1,sum(v<<(2*i) for i,v in enumerate(indices)))
class Tests(unittest.TestCase):
    def test_bc1_four_colors(self):
        got=color_block(colors());self.assertEqual(got[:4],[(255,0,0,255),(0,0,255,255),(170,0,85,255),(85,0,170,255)])
    def test_bc1_one_bit_alpha(self):
        self.assertEqual(color_block(colors(0,65535))[:4],[(0,0,0,255),(255,255,255,255),(127,127,127,255),(0,0,0,0)])
    def test_bc3_six_interpolated_alpha(self):
        alpha=bytes([240,16])+sum((i%8)<<(3*i) for i in range(16)).to_bytes(6,'little')
        self.assertEqual([x[3] for x in bc3_block(alpha+colors())[:8]],[240,16,208,176,144,112,80,48])
    def test_bc3_extreme_alpha_and_forced_four_colors(self):
        alpha=bytes([10,20])+sum((i%8)<<(3*i) for i in range(16)).to_bytes(6,'little')
        got=bc3_block(alpha+colors(0,65535));self.assertEqual([x[3] for x in got[:8]],[10,20,12,14,16,18,0,255]);self.assertEqual(got[3][:3],(170,170,170))
    def test_block_and_row_order(self):
        rgba=decode_blocks(colors(indices=[0]*16)+colors(indices=[1]*16),8,4,1)
        for y in range(4):self.assertEqual(rgba[y*32:(y+1)*32],bytes([255,0,0,255])*4+bytes([0,0,255,255])*4)
    def test_carrier_exact(self):
        rgba,report=decode(header()+colors());self.assertEqual(len(rgba),64);self.assertEqual(report['asset_id'],123);self.assertEqual(report['mips'][0]['offset'],38)
    def test_carrier_mip_chain(self):
        payload=colors()*4+colors(0,65535);rgba,report=decode(header(w=8,h=8,levels=2)+payload,1)
        self.assertEqual(report['decoded_width'],4);self.assertEqual(report['mips'][1]['offset'],70);self.assertEqual(rgba[-1],0)
    def test_all_truncation_boundaries(self):
        blob=header()+colors()
        for n in range(len(blob)):
            with self.subTest(n=n),self.assertRaises(ValueError):parse(blob[:n])
    def test_unknown_headers_and_trailing_data(self):
        blob=header()+colors()
        for at in [12,16,24,25,26,27,28,30,31,32,33,34,35,36,37]:
            b=bytearray(blob);b[at]^=0x40
            with self.subTest(at=at),self.assertRaises(ValueError):parse(bytes(b))
        with self.assertRaises(ValueError):parse(blob+b'\0')
    def test_bad_format_dimensions_shift(self):
        for fmt in [0,2,3,4,6,255]:
            with self.assertRaises(ValueError):parse(header(fmt)+colors())
        for w in [0,2,5,8192]:
            with self.assertRaises(ValueError):parse(header(w=w)+colors())
        b=bytearray(header()+colors());struct.pack_into('<I',b,8,1)
        with self.assertRaises(ValueError):parse(bytes(b))
    def test_existing_mip_bound(self):
        for level in [-1,1,1.0,True]:
            with self.assertRaises(ValueError):decode(header()+colors(),level)
    def test_exact_bc_payload(self):
        for data in [b'',colors()[:-1],colors()+b'\0']:
            with self.assertRaises(ValueError):decode_blocks(data,4,4,1)
if __name__=='__main__':unittest.main()
