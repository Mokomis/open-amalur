import copy,struct,unittest
from amalur_enums import EnumError,ROOT,CONTAINER,GROUP,NAME,VALUE,ascii_hash,compare,decimal_int32,extract_bytes,snapshot
from amalur_native_enums import extract_native,compare_to_bxml

def bxml(value=b'0',group=b'space_types',member=b'Outdoor',value_tag=96):
    nodes=[(-1,1,-1,1,0),(0,2,-1,1,1),(1,3,-1,2,2),(2,-1,-1,3,4)]
    values=[b'',group,member,value]
    attrs=[0,1,2,(96<<24)|(1<<12)|3,4,(96<<24)|(2<<12)|3,(value_tag<<24)|(3<<12)|4]
    return (struct.pack('<I',4)+b''.join(struct.pack('<5i',*n) for n in nodes)+struct.pack('<I7I',7,*attrs)
        +struct.pack('<I5I',5,ROOT,CONTAINER,GROUP,NAME,VALUE)+struct.pack('<I',4)
        +b''.join(struct.pack('<I',len(v))+v for v in values))

class EnumTests(unittest.TestCase):
    def test_strict_profile_preserves_source_literal_and_tags(self):
        result=extract_bytes(bxml());member=result['groups'][0]['members'][0]
        self.assertEqual(result['group_count'],1);self.assertEqual(member['value_int32'],0)
        self.assertEqual(member['value_field']['raw_hex'],'30');self.assertEqual(member['value_field']['type_tag'],96)
        self.assertEqual(member['value_field']['symbol_id'],VALUE)
        self.assertTrue(result['complete_structural_consumption'])
    def test_numeric_domain_has_no_float_hex_unsigned_or_whitespace_coercion(self):
        for raw in [b'0x1',b'1.0',b' 1',b'1 ',b'+1',b'01',b'-0',b'2147483648',b'-2147483649',b'']:
            with self.subTest(raw=raw):self.assertIsNone(decimal_int32(raw)[0])
        for raw,value in [(b'-2147483648',-2147483648),(b'2147483647',2147483647),(b'-1',-1)]:
            self.assertEqual(decimal_int32(raw),(value,None))
    def test_unsupported_numeric_field_is_retained_but_cannot_enter_snapshot(self):
        report=extract_bytes(bxml(b'0xff'));self.assertEqual(report['groups'][0]['members'][0]['value_field']['utf8'],'0xff')
        with self.assertRaises(EnumError):snapshot(report)
    def test_wrong_type_tag_not_interpreted_as_integer(self):
        with self.assertRaises(EnumError):extract_bytes(bxml(value_tag=97))
    def test_snapshot_contract_and_negative_signed_bits(self):
        report=extract_bytes(bxml(b'-1'));data,receipt=snapshot(report)
        self.assertEqual(data[:12],b'AENU'+struct.pack('<II',1,1));self.assertEqual(len(data),24)
        self.assertEqual(struct.unpack_from('<III',data,12),(ascii_hash('space_types'),ascii_hash('Outdoor'),0xffffffff))
        self.assertEqual(receipt['selected_source_sha256'],report['source_sha256'])
    def test_native_ascii_hash_and_case_alias_collision(self):
        self.assertEqual(ascii_hash('A'),90168);self.assertEqual(ascii_hash('outdoor'),ascii_hash('Outdoor'))
        report=extract_bytes(bxml());other=copy.deepcopy(report['groups'][0]['members'][0]);other['name']='outdoor'
        report['groups'][0]['members'].append(other)
        with self.assertRaises(EnumError):snapshot(report)
        for name in ['é','out\0door','']:
            with self.subTest(name=name),self.assertRaises((EnumError,UnicodeEncodeError)):ascii_hash(name)
    def test_variant_and_native_differences_are_not_merged(self):
        base=extract_bytes(bxml());other=extract_bytes(bxml(b'1'));difference=compare(base,other)
        self.assertEqual(len(difference['changed_in_other']),1)
        self.assertEqual(base['groups'][0]['members'][0]['value_int32'],0)
        native={'groups':[{'name':'space_types','members':[{'name':'Outdoor','value_int32':7},{'name':'Interior','value_int32':1}]}]}
        diff=compare_to_bxml(native,base);self.assertEqual(len(diff['native_only']),1)
        self.assertEqual(diff['different_values'][0]['native_value'],7)
    def test_native_executable_hash_is_required_before_parsing(self):
        with self.assertRaisesRegex(EnumError,'SHA256'):extract_native(b'not the selected executable')

if __name__=='__main__':unittest.main()
