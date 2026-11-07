"""Batch directory/member invariants and hash-bound real Windows containers."""
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from amalur_script import (Limits,ParseError,disassemble,inspect_bundle_bytes,
                           iter_bundle_bytes,iter_bundle_file,main,parse_bundle_bytes,parse_bytes)
from test_amalur_script import chunk,function,wrapper


def batch(entries):
    return (struct.pack('<I',len(entries))
            +b''.join(struct.pack('<II',ident,len(raw)) for ident,raw in entries)
            +b''.join(raw for _,raw in entries))


class BatchContainerTests(unittest.TestCase):
    def fixture(self):
        return [(12842,wrapper(chunk(),b'first')),
                (12886,wrapper(chunk(function(constants=[b'\x01\x01'])),b'second',(b'reference',)))]

    def test_directory_lengths_members_and_exact_consumption(self):
        entries=self.fixture();raw=batch(entries);result=parse_bundle_bytes(raw)
        self.assertEqual(result['member_count'],2)
        self.assertEqual(result['directory_bytes'],20)
        self.assertEqual(result['container_bytes_consumed'],len(raw))
        self.assertEqual(result['summary'],{'functions':2,'instructions':2,'constants':1})
        self.assertEqual([m['wrapper']['name'] for m in result['members']],['first','second'])
        self.assertEqual([e['resource_id'] for e in result['directory']],[12842,12886])
        self.assertEqual([e['declared_member_bytes'] for e in result['directory']],[len(v) for _,v in entries])

    def test_member_hashes_and_absolute_offsets_preserved(self):
        entries=self.fixture();raw=batch(entries);result=parse_bundle_bytes(raw)
        offset=20
        for (_,source),member in zip(entries,result['members']):
            isolated=parse_bytes(source)
            self.assertEqual(member['input_sha256'],hashlib.sha256(source).hexdigest())
            self.assertEqual(member['payload_sha256'],isolated['payload_sha256'])
            self.assertEqual(member['container']['payload_sha256'],isolated['payload_sha256'])
            self.assertEqual(member['container']['input_sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(member['container']['member_file_offset'],offset)
            self.assertEqual(member['wrapper']['payload_file_offset'],offset+isolated['wrapper']['payload_file_offset'])
            self.assertEqual(member['chunk']['root_function']['code_file_offset'],offset+isolated['chunk']['root_function']['code_file_offset'])
            offset+=len(source)

    def test_directory_only_inspection_does_not_claim_member_parse(self):
        raw=batch([(1,b'not-a-valid-wrapper')])
        inspected=inspect_bundle_bytes(raw)
        self.assertNotIn('members',inspected)
        self.assertIn('not performed',inspected['coverage'])
        with self.assertRaises(ParseError):parse_bundle_bytes(raw)

    def test_same_bytecode_different_wrapper_preserves_both_identities(self):
        first=wrapper(chunk(),b'first')
        second=wrapper(chunk(),b'second',(b'bound_reference',))
        result=parse_bundle_bytes(batch([(1,first),(2,second)]))
        a,b=result['members']
        self.assertNotEqual(a['input_sha256'],b['input_sha256'])
        self.assertEqual(a['payload_sha256'],b['payload_sha256'])
        self.assertNotEqual(a['wrapper'],b['wrapper'])

    def test_every_truncated_batch_prefix_is_rejected(self):
        raw=batch(self.fixture())
        for size in range(len(raw)):
            with self.subTest(size=size),self.assertRaises(ParseError):
                parse_bundle_bytes(raw[:size])

    def test_trailing_bytes_are_not_padding(self):
        with self.assertRaisesRegex(ParseError,'exactly consume'):
            parse_bundle_bytes(batch(self.fixture())+b'\x00')

    def test_member_boundaries_are_not_recovered_by_magic_scanning(self):
        raw=bytearray(batch(self.fixture()))
        first=struct.unpack_from('<I',raw,8)[0]
        second=struct.unpack_from('<I',raw,16)[0]
        struct.pack_into('<I',raw,8,first+1)
        struct.pack_into('<I',raw,16,second-1)
        with self.assertRaisesRegex(ParseError,'payload size'):
            parse_bundle_bytes(bytes(raw))

    def test_duplicate_resource_ids_are_outside_admitted_directory(self):
        member=wrapper(chunk())
        with self.assertRaisesRegex(ParseError,'duplicate resource'):
            parse_bundle_bytes(batch([(7,member),(7,member)]))

    def test_empty_batch_and_excessive_member_count_rejected(self):
        for count in [0,4097,0xffffffff]:
            with self.subTest(count=count),self.assertRaisesRegex(ParseError,'member count'):
                inspect_bundle_bytes(struct.pack('<I',count))
        with self.assertRaisesRegex(ParseError,'member count'):
            parse_bundle_bytes(batch(self.fixture()),Limits(max_bundle_members=1))

    def test_short_directory_and_member_rejected(self):
        with self.assertRaisesRegex(ParseError,'directory cannot fit'):
            inspect_bundle_bytes(struct.pack('<I',2)+b'\x00'*8)
        with self.assertRaisesRegex(ParseError,'shorter than'):
            inspect_bundle_bytes(batch([(1,b'\x00'*11)]))

    def test_raw_chunk_is_not_a_wrapped_batch_member(self):
        with self.assertRaisesRegex(ParseError,'ordinary script wrapper'):
            parse_bundle_bytes(batch([(1,chunk())]))

    def test_bundle_file_limit_is_enforced_before_member_work(self):
        raw=batch(self.fixture())
        with self.assertRaisesRegex(ParseError,'file exceeds'):
            parse_bundle_bytes(raw,Limits(max_file_bytes=len(raw)-1))

    def test_aggregate_function_limit_and_partial_iterator_failure(self):
        raw=batch(self.fixture());iterator=iter_bundle_bytes(raw,Limits(max_bundle_functions=1))
        first=next(iterator)
        self.assertEqual(first['wrapper']['name'],'first')
        with self.assertRaisesRegex(ParseError,'aggregate functions'):
            next(iterator)

    def test_aggregate_instruction_and_constant_limits(self):
        entries=[(1,wrapper(chunk(function(constants=[b'\x00'])))),
                 (2,wrapper(chunk(function(constants=[b'\x00']))))]
        for limits,reason in [(Limits(max_instructions=1),'instructions'),(Limits(max_constants=1),'constants')]:
            with self.subTest(reason=reason),self.assertRaisesRegex(ParseError,'aggregate '+reason):
                parse_bundle_bytes(batch(entries),limits)

    def test_each_member_still_enforces_its_function_budget(self):
        raw=batch([(1,wrapper(chunk(function(children=[function()]))))])
        with self.assertRaisesRegex(ParseError,'function count'):
            parse_bundle_bytes(raw,Limits(max_functions=1))

    def test_nested_errors_report_container_offsets(self):
        entries=self.fixture();bad=bytearray(entries[1][1])
        isolated=parse_bytes(bytes(bad));code=isolated['chunk']['root_function']['code_file_offset']
        bad[code:code+4]=b'\xff'*4
        raw=batch([entries[0],(entries[1][0],bytes(bad))])
        with self.assertRaises(ParseError) as caught:
            parse_bundle_bytes(raw)
        self.assertEqual(caught.exception.offset,20+len(entries[0][1])+code)

    def test_cli_bundle_keeps_members_separate(self):
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'batch.bin';output=Path(folder)/'batch.json';listing=Path(folder)/'batch.txt'
            raw=batch(self.fixture());source.write_bytes(raw)
            with patch.object(sys,'argv',['amalur_script',str(source),'--bundle','--output',str(output),'--disassembly',str(listing)]),patch('sys.stdout',new_callable=io.StringIO):
                main()
            result=json.loads(output.read_text())
            self.assertEqual(len(result['members']),2)
            self.assertIn('MEMBER 0 resource=12842',listing.read_text())
            self.assertIn('MEMBER 1 resource=12886',listing.read_text())
            self.assertEqual(source.read_bytes(),raw)


if __name__=='__main__':unittest.main(verbosity=2)
