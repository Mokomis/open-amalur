"""Exact serialized uint64 provenance stays distinct from native tag packing."""
import json
import unittest
from amalur_script import parse_bytes
from test_amalur_script import chunk, function


class Uint64EncodingTests(unittest.TestCase):
    def test_maximum_uint64_bytes_survive_parser_and_json_before_normalization(self):
        raw_values=[bytes.fromhex('ffffffffffffffff'),bytes.fromhex('fffffffffffffff0')]
        fixture=chunk(function(constants=[b'\x0b'+raw for raw in raw_values]))
        parsed=parse_bytes(fixture)
        constants=parsed['chunk']['root_function']['constants']
        self.assertEqual([c['type_id'] for c in constants],[11,11])
        self.assertEqual([c['value'] for c in constants],[2**64-1,2**64-16])
        self.assertEqual([c['raw_hex'] for c in constants],['ffffffffffffffff','fffffffffffffff0'])
        self.assertEqual([c['native_packed_hex'] for c in constants],['fffffffffffffffb']*2)
        for constant,raw in zip(constants,raw_values):
            at=constant['file_offset']
            self.assertEqual(fixture[at:at+9],b'\x0b'+raw)
            self.assertEqual(bytes.fromhex(constant['raw_hex']),raw)
        restored=json.loads(json.dumps(parsed))['chunk']['root_function']['constants']
        self.assertEqual([c['raw_hex'] for c in restored],['ffffffffffffffff','fffffffffffffff0'])
        self.assertEqual([c['native_packed_hex'] for c in restored],['fffffffffffffffb']*2)


if __name__=='__main__':unittest.main(verbosity=2)
