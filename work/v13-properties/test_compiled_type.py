"""Synthetic contract/bounds checks, not original-game behavior tests."""
import struct
import unittest
from compiled_type import decode_compiled_type, CompiledTypeError


def fixture():
    p = bytearray(96)
    struct.pack_into('<I', p, 0x10, 237033)
    struct.pack_into('<II', p, 0x14, 8 + 48, 1)
    struct.pack_into('<I', p, 0x20, 226948)
    struct.pack_into('<III', p, 0x24, 8 + 56, 2, 8 + 80)
    struct.pack_into('<I', p, 48, 123)
    struct.pack_into('<III', p, 56, 34, 8 + 88, 2)
    struct.pack_into('<II', p, 68, 22, 456)
    struct.pack_into('<II', p, 80, 0, 12)
    struct.pack_into('<II', p, 88, 100, 200)
    tail = struct.pack('<4I', 0x14, 0x24, 0x2c, 60)
    return struct.pack('<II', len(p), len(tail)) + p + tail


NAMES = {22: 'PartCustomInteractionBlueprint', 34: 'PartInteractionBlueprint'}


class ContractTests(unittest.TestCase):
    def test_confirmed_reference_fields_and_input_unchanged(self):
        b = fixture()
        d = decode_compiled_type(b, NAMES)
        self.assertEqual(d['script_key_u32'], 237033)
        self.assertEqual(d['parent_key_u32'], 226948)
        self.assertEqual(d['dependency_keys_u32'], [123])
        self.assertEqual(d['components'][0]['reference_keys_u32'], [100, 200])
        self.assertEqual(d['components'][1]['reference_key_u32'], 456)
        self.assertEqual(b, fixture())

    def test_every_truncation_rejected(self):
        b = fixture()
        for n in range(len(b)):
            with self.subTest(n=n), self.assertRaises(CompiledTypeError):
                decode_compiled_type(b[:n], NAMES)

    def test_pointer_count_offset_and_kind_corruption(self):
        for offset, value in [(0x14, 0xffffffff), (0x18, 100001),
                              (0x24, 0xffffffff), (0x28, 4097),
                              (0x2c, 0xffffffff), (56, 43), (60, 1),
                              (64, 100001), (80, 0xffffffff)]:
            b = bytearray(fixture())
            struct.pack_into('<I', b, 8 + offset, value)
            with self.subTest(offset=offset), self.assertRaises(CompiledTypeError):
                decode_compiled_type(bytes(b), NAMES)

    def test_nonempty_reference_requires_relocation(self):
        b = bytearray(fixture())
        struct.pack_into('<I', b, len(b) - 4, 64)
        with self.assertRaisesRegex(CompiledTypeError, 'lacks native relocation'):
            decode_compiled_type(bytes(b), NAMES)

    def test_compact_workbench_is_not_claimed_as_compiled(self):
        raw = bytes.fromhex('847603000100000099fb3700ffffffffe99d030004081700000000000000000084')
        with self.assertRaisesRegex(CompiledTypeError, 'compact SimType conversion is unresolved'):
            decode_compiled_type(raw, NAMES)


if __name__ == '__main__':
    unittest.main()
