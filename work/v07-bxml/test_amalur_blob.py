import struct
import unittest
from amalur_blob import BlobError, Limits, parse_bytes

def carrier(payload,slots):
    tail=b''.join(struct.pack('<I',slot) for slot in slots)
    return struct.pack('<II',len(payload),len(tail))+payload+tail

class BlobTests(unittest.TestCase):
    def test_exact_spans_and_slot_words(self):
        payload=struct.pack('<IIII',8,1,12,99)
        result=parse_bytes(carrier(payload,[0,8]))
        self.assertEqual(result['tail']['file_offset'],24)
        self.assertEqual(result['slots'][0]['target_file_offset'],8)
        self.assertEqual(result['slots'][0]['target_payload_offset'],0)
        self.assertEqual(result['slots'][0]['following_word_u32'],1)
        self.assertEqual(result['slots'][1]['word_u32'],12)
        self.assertFalse(result['payload_semantics_decoded'])
    def test_length_mismatch_rejected(self):
        for data in [b'',b'\0'*7,struct.pack('<II',10,4)+b'\0'*10]:
            with self.assertRaises(BlobError):parse_bytes(data)
    def test_tail_width_rejected(self):
        with self.assertRaises(BlobError):parse_bytes(struct.pack('<II',0,1)+b'\0')
    def test_slot_bounds_rejected(self):
        for slot in [1,4,0xffffffff]:
            with self.assertRaises(BlobError):parse_bytes(carrier(b'\0'*4,[slot]))
    def test_out_of_range_word_is_preserved_without_pointer_claim(self):
        result=parse_bytes(carrier(struct.pack('<I',0xffffffff),[0]))
        self.assertEqual(result['slots'][0]['word_u32'],0xffffffff)
        self.assertFalse(result['slots'][0]['relocated_target_in_payload'])
        self.assertIsNone(result['slots'][0]['following_word_u32'])
    def test_duplicate_and_unaligned_slots_reported(self):
        result=parse_bytes(carrier(b'\0'*9,[1,1]))
        self.assertEqual(result['summary']['unique_relocation_slots'],1)
        self.assertEqual(result['summary']['slots_unaligned_mod4'],2)
        self.assertEqual(result['summary']['duplicate_slots'],[{'slot_payload_offset':1,'occurrences':2}])
    def test_empty_carrier_retained(self):
        result=parse_bytes(carrier(b'',[]))
        self.assertTrue(result['complete_carrier_consumption'])
        self.assertEqual(result['summary']['relocation_slots'],0)
    def test_native_minus_eight_boundary(self):
        for stored,offset,inside in [(0,-8,False),(7,-1,False),(8,0,True),(11,3,True),(12,4,False)]:
            with self.subTest(stored=stored):
                result=parse_bytes(carrier(struct.pack('<I',stored),[0]))
                slot=result['slots'][0]
                self.assertEqual(slot['target_payload_offset'],offset)
                self.assertEqual(slot['target_file_offset'],stored)
                self.assertEqual(slot['relocated_target_in_payload'],inside)
    def test_explicit_limits(self):
        data=carrier(b'\0'*4,[0])
        with self.assertRaises(BlobError):parse_bytes(data,Limits(max_file_bytes=8))
        with self.assertRaises(BlobError):parse_bytes(data,Limits(max_slots=0))

if __name__=='__main__':unittest.main()
