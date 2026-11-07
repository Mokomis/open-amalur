import struct
import unittest
from amalur_render_inventory import PROFILES,parse_bytes
from amalur_scene import SceneError

def fixture():
    payload=bytearray(544);struct.pack_into('<I',payload,0,524859)
    for slot,stride,label in PROFILES:
        count=2 if stride==84 else 1
        at=len(payload);struct.pack_into('<II',payload,slot,at+8,count)
        for index in range(count):
            record=bytearray(stride)
            if stride==84:
                struct.pack_into('<4f4f4f3fII',record,0,1,2,3,4,10,20,30,1,0,0,0,1,1,1,1,94,290531)
            payload+=record
    return struct.pack('<II',len(payload),4*len(PROFILES))+payload+b''.join(struct.pack('<I',p[0]) for p in PROFILES)

class InventoryTests(unittest.TestCase):
    def test_report_preserves_duplicate_records_and_provenance(self):
        result=parse_bytes(fixture());render=[a for a in result['arrays'] if a['assumed_stride_bytes']==84]
        self.assertEqual(result['summary']['candidate_render_records'],6)
        self.assertEqual(result['resource_ids_at_render_offset_64'],[290531])
        self.assertEqual(len(result['same_transform_flags_resource_groups']),1)
        self.assertEqual(len(result['same_transform_flags_resource_groups'][0]),6)
        self.assertEqual(render[0]['exact_duplicate_groups'],[[0,1]])
        self.assertEqual(len(render[0]['records']),2)
        self.assertEqual(len(render[0]['records'][0]['raw_hex']),168)
    def test_bounds_are_enforced(self):
        data=bytearray(fixture());struct.pack_into('<II',data,8+0x150,len(data)-4,100)
        with self.assertRaises(SceneError):parse_bytes(bytes(data))
    def test_missing_relocation_slot_rejected(self):
        data=bytearray(fixture());struct.pack_into('<I',data,len(data)-4,0)
        with self.assertRaises(SceneError):parse_bytes(bytes(data))
    def test_nonfinite_hypothesis_is_preserved_as_bits(self):
        data=bytearray(fixture());target=struct.unpack_from('<I',data,8+0x150)[0]
        struct.pack_into('<I',data,target,0x7fc00000)
        result=parse_bytes(bytes(data));record=next(a for a in result['arrays'] if a['slot_payload_offset']==0x150)['records'][0]
        self.assertEqual(record['inferred']['sphere_xyz_radius'][0],{'nonfinite_bits':'0000c07f'})
    def test_overlapping_guessed_arrays_rejected(self):
        data=bytearray(fixture());target=struct.unpack_from('<I',data,8+0x150)[0]
        struct.pack_into('<I',data,8+0x160,target)
        with self.assertRaises(SceneError):parse_bytes(bytes(data))

if __name__=='__main__':unittest.main()
