"""Synthetic malformed-input and provenance checks, run on Windows by parent."""
import csv
import io
import json
import struct
import tempfile
import unittest
from pathlib import Path
from amalur_bxml import BxmlError, Limits, load_symbols, parse_bytes, parse_file

def fixture(nodes=None, attributes=None, symbols=None, values=None, trailer=b'\0'*4):
    nodes = [(-1,-1,-1,1,0)] if nodes is None else nodes
    attributes = [0x01000000] if attributes is None else attributes
    symbols = [123456] if symbols is None else symbols
    values = [b'opaque'] if values is None else values
    data = bytearray(struct.pack('<I',len(nodes)))
    for node in nodes: data += struct.pack('<iiiii',*node)
    data += struct.pack('<I',len(attributes))
    for attribute in attributes: data += struct.pack('<I',attribute)
    data += struct.pack('<I',len(symbols))
    for symbol in symbols: data += struct.pack('<I',symbol)
    data += struct.pack('<I',len(values))
    for value in values: data += struct.pack('<I',len(value))+value
    return bytes(data)+trailer

class BxmlTests(unittest.TestCase):
    def test_literal_raw_bytes_and_unknown_tags(self):
        result=parse_bytes(fixture(attributes=[0xfe000000], values=[b'\xff\0\x81']))
        self.assertIsNone(result['values'][0]['utf8'])
        self.assertEqual(result['values'][0]['raw_hex'],'ff0081')
        self.assertEqual(result['attributes'][0]['type_tag'],254)
        self.assertTrue(result['complete_consumption'])
    def test_nul_utf8_is_retained(self):
        result=parse_bytes(fixture(values=[b'a\0b']))
        self.assertEqual(result['values'][0]['utf8'],'a\0b')
        self.assertEqual(result['values'][0]['bytes'],3)
    def test_sentinels_are_distinct_from_empty_value(self):
        result=parse_bytes(fixture(nodes=[(-1,-1,-1,2,0)],attributes=[0x01ffffff,0x01000000],values=[b'']))
        self.assertIsNone(result['attributes'][0]['name_symbol_id'])
        self.assertTrue(result['attributes'][0]['value_missing'])
        self.assertFalse(result['attributes'][1]['value_missing'])
        self.assertEqual(result['values'][0]['utf8'],'')
    def test_unambiguous_symbol_name(self):
        result=parse_bytes(fixture(),{123456:['scene_name']})
        self.assertEqual(result['attributes'][0]['name'],'scene_name')
    def test_ambiguous_symbol_never_selects_a_winner(self):
        result=parse_bytes(fixture(),{123456:['first','second']})
        self.assertIsNone(result['attributes'][0]['name'])
        self.assertEqual(result['attributes'][0]['name_candidates'],['first','second'])
    def test_zero_and_absent_trailers_are_explicit(self):
        self.assertEqual(parse_bytes(fixture())['trailer']['profile'],'one zero uint32')
        self.assertEqual(parse_bytes(fixture(trailer=b''))['trailer']['profile'],'no trailer')
    def test_unknown_trailer_rejected(self):
        for trailer in [b'\0',b'\1\0\0\0',b'\0'*8]:
            with self.subTest(trailer=trailer),self.assertRaises(BxmlError): parse_bytes(fixture(trailer=trailer))
    def test_every_truncation_rejected_except_exact_trailer_boundary(self):
        data=fixture()
        for length in range(len(data)):
            if length==len(data)-4: continue
            with self.subTest(length=length),self.assertRaises(BxmlError): parse_bytes(data[:length])
    def test_negative_count_is_bounded_before_allocation(self):
        with self.assertRaises(BxmlError): parse_bytes(b'\xff'*4)
    def test_node_limit(self):
        with self.assertRaises(BxmlError): parse_bytes(fixture(),limits=Limits(max_nodes=0))
    def test_file_limit(self):
        with self.assertRaises(BxmlError): parse_bytes(fixture(),limits=Limits(max_file_bytes=3))
    def test_value_limit(self):
        with self.assertRaises(BxmlError): parse_bytes(fixture(),limits=Limits(max_value_bytes=2))
    def test_symbol_index_bounds(self):
        with self.assertRaises(BxmlError): parse_bytes(fixture(attributes=[0x01000001]))
    def test_value_index_bounds(self):
        with self.assertRaises(BxmlError): parse_bytes(fixture(attributes=[0x01001000]))
    def test_attribute_overlap_rejected(self):
        with self.assertRaises(BxmlError): parse_bytes(fixture(nodes=[(-1,1,-1,1,0),(0,-1,-1,1,0)]))
    def test_unowned_attribute_rejected(self):
        with self.assertRaises(BxmlError): parse_bytes(fixture(nodes=[(-1,-1,-1,0,0)]))
    def test_invalid_attribute_range_rejected(self):
        with self.assertRaises(BxmlError): parse_bytes(fixture(nodes=[(-1,-1,-1,2,0)]))
    def test_invalid_parent_rejected(self):
        with self.assertRaises(BxmlError): parse_bytes(fixture(nodes=[(9,-1,-1,1,0)]))
    def test_sibling_cycle_rejected(self):
        nodes=[(-1,1,-1,0,0),(0,-1,2,0,0),(0,-1,1,0,0)]
        with self.assertRaises(BxmlError): parse_bytes(fixture(nodes,[],[],[]))
    def test_parent_cycle_without_roots_rejected(self):
        nodes=[(1,1,-1,0,0),(0,0,-1,0,0)]
        with self.assertRaises(BxmlError): parse_bytes(fixture(nodes,[],[],[]))
    def test_parent_chain_disagreement_rejected(self):
        nodes=[(-1,1,-1,0,0),(-1,-1,-1,0,0)]
        with self.assertRaises(BxmlError): parse_bytes(fixture(nodes,[],[],[]))
    def test_missing_child_membership_rejected(self):
        nodes=[(-1,-1,-1,0,0),(0,-1,-1,0,0)]
        with self.assertRaises(BxmlError): parse_bytes(fixture(nodes,[],[],[]))
    def test_deep_graph_is_iterative(self):
        count=5000
        nodes=[(i-1,i+1 if i+1<count else -1,-1,0,0) for i in range(count)]
        result=parse_bytes(fixture(nodes,[],[],[]))
        self.assertEqual(result['summary']['maximum_depth'],count-1)
    def test_forest_retained_without_inventing_root_order(self):
        result=parse_bytes(fixture([(-1,-1,-1,0,0),(-1,-1,-1,0,0)],[],[],[]))
        self.assertEqual(result['summary']['root_indices'],[0,1])
    def test_selected_span_has_absolute_offsets_and_full_source_identity(self):
        import hashlib
        data=b'header!!'+fixture()+b'tail'
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'scene.bin';path.write_bytes(data)
            result=parse_file(path,offset=8,length=len(fixture()))
        self.assertEqual(result['input_sha256'],hashlib.sha256(data).hexdigest())
        self.assertEqual(result['section_sha256'],hashlib.sha256(fixture()).hexdigest())
        self.assertEqual(result['nodes'][0]['file_offset'],12)
        self.assertFalse(result['source_span']['whole_file'])
    def test_invalid_span_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'bxml';path.write_bytes(fixture())
            for offset,length in [(-1,2),(1,-1),(9999,1),(0,9999)]:
                with self.subTest(offset=offset,length=length),self.assertRaises(BxmlError):
                    parse_file(path,offset=offset,length=length)
    def test_csv_conflicts_and_comma_labels_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            a=Path(directory)/'a.csv';b=Path(directory)/'b.csv'
            a.write_text('id,name\n123456,"name, with comma"\n',encoding='utf-8')
            b.write_text('123456,other\n',encoding='utf-8')
            labels,report=load_symbols([a,b])
        self.assertEqual(labels[123456],['name, with comma','other'])
        self.assertEqual(len(report['conflicts']),1)
    def test_invalid_csv_id_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'a.csv';path.write_text('4294967296,bad\n',encoding='utf-8')
            with self.assertRaises(BxmlError): load_symbols([path])

if __name__=='__main__': unittest.main()
