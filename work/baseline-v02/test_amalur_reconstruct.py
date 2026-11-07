"""Synthetic reconstruction obligations; run on the Windows host."""
import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from amalur_script import decode_instruction
from amalur_reconstruct import ReconstructionError, lua_bytes, reconstruct


def ins(op,a=0,b=0,c=0,bx=None,pc=0):
    word = (op << 25) | a | (((b << 9) | c) << 8 if bx is None else bx << 8)
    return decode_instruction(word,0x100+pc*4,pc)


def fn(code,constants=(),children=(),params=0,stack=8,upvalues=0):
    return {'instructions': [dict(row,pc=i,file_offset=0x100+i*4) for i,row in enumerate(code)],
            'constants':list(constants),'children':list(children),'parameter_count':params,
            'maximum_stack_size':stack,'upvalue_count':upvalues,'vararg_flags':0}


def parsed(function):
    return {'input_sha256':'0'*64,'chunk':{'root_function':function}}


def string(value):
    return {'type':'string','value':{'bytes_hex':value.encode().hex()}}


def profile():
    semantics={7:('move',0),25:('loadk',0),85:('getglobal',1),27:('setglobal',0),
               67:('getfield_k',2),2:('call_fixed',0),9:('return_fixed',0),
               60:('closure_no_upvalues',0),28:('jump',0)}
    p={'schema_version':1,'binary_sha256':'1'*64,'inline_data_opcode':70,
       'instruction_layout':{'confirmation':'native_static','evidence':['synthetic-test-fixture']},
       'number_encoding':{'confirmation':'native_static','kind':'signed_int32','evidence':['synthetic-test-fixture']},
       'opcodes':{}}
    for op,(kind,skip) in semantics.items():
        p['opcodes'][str(op)]={'kind':kind,'inline_data_words':skip,
                              'confirmation':'native_static','evidence':['synthetic-test-fixture']}
    return p


class ReconstructionTests(unittest.TestCase):
    def test_string_literal_preserves_arbitrary_bytes(self):
        self.assertEqual(lua_bytes('002231ff5c'), '"\\000\\"1\\255\\\\"')

    def test_straight_line_reads_writes_and_source(self):
        f=fn([ins(25,a=1,bx=0),ins(7,a=2,b=1),ins(9,a=2,b=2)], [string('hello')])
        ir,lua=reconstruct(parsed(f),profile())
        self.assertEqual(ir['summary']['emittable_function_bodies'],1)
        self.assertIn('r1 = "hello"',lua)
        self.assertIn('r2 = r1',lua)
        self.assertIn('return r2',lua)
        self.assertEqual(ir['root_function']['instructions'][1]['reads'],[1])
        self.assertEqual(ir['root_function']['blocks'][0]['instruction_pcs'],[0,1,2])

    def test_inline_data_is_consumed_only_by_confirmed_owner(self):
        f=fn([ins(85,a=0,bx=0),ins(70),ins(67,a=1,b=0,c=1),ins(70),ins(70),ins(9,b=1)],
             [string('object'),string('field')])
        ir,lua=reconstruct(parsed(f),profile())
        rows=ir['root_function']['instructions']
        self.assertEqual([r['pc'] for r in rows],[0,2,5])
        self.assertEqual(rows[1]['metadata_pcs'],[3,4])
        self.assertEqual([w['word_hex'] for w in rows[1]['metadata_words']],['8c000000','8c000000'])
        self.assertEqual(rows[0]['successors'],[2])
        self.assertIn('r1 = r0["field"]',lua)

    def test_missing_data_rejected(self):
        f=fn([ins(85,bx=0),ins(9,b=1)],[string('x')])
        with self.assertRaisesRegex(ReconstructionError,'expected inline DATA'):
            reconstruct(parsed(f),profile())

    def test_inline_global_cache_slot_extent_checked(self):
        p=profile();p['opcodes']['85']['inline_cache_constant_slots']=2
        constants=[string('object'),{'type':'nil'},{'type':'nil'}]
        good=fn([ins(85,bx=0),ins(70,bx=1),ins(9,b=1)],constants)
        ir,_=reconstruct(parsed(good),p)
        self.assertEqual(ir['root_function']['instructions'][0]['cache_constant_indices'],[1,2])
        bad=fn([ins(85,bx=0),ins(70,bx=2),ins(9,b=1)],constants)
        with self.assertRaisesRegex(ReconstructionError,'cache constant slots outside pool'):
            reconstruct(parsed(bad),p)

    def test_truncated_data_rejected(self):
        with self.assertRaisesRegex(ReconstructionError,'inline data exceeds'):
            reconstruct(parsed(fn([ins(85)], [string('x')])),profile())

    def test_cached_field_requires_immediate_producer(self):
        p=profile();p['opcodes']['67']['kind']='getfield_cached_k'
        p['opcodes']['85']['produces_cached_result']=True
        f=fn([ins(85,a=2,bx=0),ins(70),ins(67,a=1,b=2,c=1),ins(70),ins(70),ins(9,b=1)],
             [string('object'),string('field')])
        ir,lua=reconstruct(parsed(f),p)
        self.assertEqual(ir['summary']['emittable_function_bodies'],1)
        self.assertEqual(ir['root_function']['instructions'][1]['cached_result_producer_pc'],0)
        self.assertIn('r1 = r2["field"]',lua)

    def test_cached_field_high_operand_flag_is_unsupported(self):
        p=profile();p['opcodes']['67']['kind']='getfield_cached_k'
        p['opcodes']['85']['produces_cached_result']=True
        f=fn([ins(85,a=2,bx=0),ins(70),ins(67,a=1,b=2,c=257),ins(70),ins(70),ins(9,b=1)],
             [string('object'),string('field')])
        ir,lua=reconstruct(parsed(f),p)
        self.assertEqual(ir['summary']['emittable_function_bodies'],0)
        self.assertNotIn('r1 = r2["field"]',lua)

    def test_cached_field_without_last_result_proof_is_stub(self):
        p=profile();p['opcodes']['67']['kind']='getfield_cached_k'
        f=fn([ins(67,a=1,b=2,c=0),ins(70),ins(70),ins(9,b=1)],[string('field')])
        ir,lua=reconstruct(parsed(f),p)
        self.assertEqual(ir['summary']['emittable_function_bodies'],0)
        self.assertNotIn('r1 = r2["field"]',lua)

    def test_unconfirmed_opcode_becomes_explicit_stub(self):
        p=profile();p['opcodes']['7']['confirmation']='provisional'
        ir,lua=reconstruct(parsed(fn([ins(7),ins(9,b=1)])),p)
        self.assertEqual(ir['summary']['unresolved_function_bodies'],1)
        self.assertIn('UNRESOLVED',lua)
        self.assertIn('__unresolved(',lua)
        self.assertNotIn('r0 = r0',lua)

    def test_unconfirmed_layout_prevents_emission(self):
        p=profile();p['instruction_layout']['confirmation']='provisional'
        ir,lua=reconstruct(parsed(fn([ins(9,b=1)])),p)
        self.assertEqual(ir['summary']['emittable_function_bodies'],0)

    def test_unknown_opcode_has_unknown_successors(self):
        ir,_=reconstruct(parsed(fn([ins(70),ins(9,b=1)])),profile())
        self.assertIsNone(ir['root_function']['instructions'][0]['successors'])

    def test_unknown_number_interpretation_stubs_function(self):
        p=profile();p.pop('number_encoding')
        f=fn([ins(25,bx=0),ins(9,b=2)],[{'type':'number','raw_hex':'000000c8'}])
        ir,lua=reconstruct(parsed(f),p)
        self.assertEqual(ir['summary']['emittable_function_bodies'],0)
        self.assertNotIn('r0 = 200',lua)

    def test_signed_number_exact(self):
        f=fn([ins(25,bx=0),ins(9,b=2)],[{'type':'number','raw_hex':'ffffffff'}])
        _,lua=reconstruct(parsed(f),profile())
        self.assertIn('r0 = -1',lua)

    def test_fixed_call_argument_and_result_ranges(self):
        f=fn([ins(2,a=1,b=3,c=3),ins(9,b=1)],params=4)
        ir,lua=reconstruct(parsed(f),profile())
        row=ir['root_function']['instructions'][0]
        self.assertEqual(row['reads'],[1,2,3])
        self.assertEqual(row['writes'],[1,2])
        self.assertIn('r1, r2 = r1(r2, r3)',lua)

    def test_undefined_register_read_is_not_fabricated_as_nil(self):
        ir,lua=reconstruct(parsed(fn([ins(7,a=1,b=0),ins(9,b=1)])),profile())
        self.assertEqual(ir['summary']['emittable_function_bodies'],0)
        self.assertIn('register read before a known definition',lua)

    def test_open_calls_and_returns_are_not_silently_fixed(self):
        for op,b,c in [(2,0,1),(2,2,0),(9,0,0)]:
            with self.subTest(op=op,b=b,c=c):
                code=[ins(op,b=b,c=c)] + ([] if op==9 else [ins(9,b=1)])
                ir,_=reconstruct(parsed(fn(code)),profile())
                self.assertEqual(ir['summary']['emittable_function_bodies'],0)

    def test_call_high_operand_flag_is_explicitly_unsupported(self):
        ir,_=reconstruct(parsed(fn([ins(2,a=0,b=1,c=257),ins(9,b=1)],params=1)),profile())
        self.assertEqual(ir['summary']['emittable_function_bodies'],0)
        self.assertEqual(ir['root_function']['instructions'][0]['status'],'unsupported_operands')

    def test_register_out_of_bounds_rejected(self):
        with self.assertRaisesRegex(ReconstructionError,'outside stack'):
            reconstruct(parsed(fn([ins(7,a=8,b=0),ins(9,b=1)],stack=8)),profile())

    def test_child_is_nested_and_global_environment_read_at_each_access(self):
        child=fn([ins(9,b=1)],stack=1)
        root=fn([ins(60,bx=0),ins(27,bx=0),ins(9,b=1)],[string('callback')],[child])
        ir,lua=reconstruct(parsed(root),profile())
        self.assertEqual(ir['summary']['emittable_function_bodies'],2)
        self.assertIn('r0 = function()',lua)
        self.assertIn('__getfenv(1)["callback"] = r0',lua)

    def test_captured_upvalues_are_not_fabricated(self):
        child=fn([ins(9,b=1)],upvalues=1)
        root=fn([ins(60,bx=0),ins(9,b=1)],children=[child])
        ir,_=reconstruct(parsed(root),profile())
        self.assertEqual(ir['summary']['emittable_function_bodies'],0)

    def test_jump_edges_and_blocks_retained_but_source_stubs(self):
        f=fn([ins(28,bx=65536),ins(7),ins(9,b=1)])
        ir,lua=reconstruct(parsed(f),profile())
        self.assertEqual(ir['root_function']['instructions'][0]['successors'],[2])
        self.assertEqual([b['start_pc'] for b in ir['root_function']['blocks']],[0,1,2])
        self.assertIn('UNRESOLVED',lua)

    def test_jump_into_metadata_rejected(self):
        f=fn([ins(28,bx=65536),ins(85,bx=0),ins(70),ins(9,b=1)],[string('x')])
        with self.assertRaisesRegex(ReconstructionError,'edge enters inline data'):
            reconstruct(parsed(f),profile())

    def test_instructions_after_return_not_emitted_as_invalid_lua(self):
        ir,_=reconstruct(parsed(fn([ins(9,b=1),ins(7),ins(9,b=1)])),profile())
        self.assertEqual(ir['summary']['emittable_function_bodies'],0)

    def test_empty_code_and_excessive_local_count_are_stubs(self):
        for f in (fn([]),fn([ins(9,b=1)],stack=200)):
            ir,_=reconstruct(parsed(f),profile())
            self.assertEqual(ir['summary']['emittable_function_bodies'],0)

    def test_unknown_vararg_flags_are_explicitly_unsupported(self):
        for flags in (1,3,4,255):
            f=fn([ins(9,b=1)]);f['vararg_flags']=flags
            ir,lua=reconstruct(parsed(f),profile())
            self.assertEqual(ir['summary']['emittable_function_bodies'],0)
            self.assertIn('unsupported vararg flags',lua)

    def test_invalid_semantic_profile_rejected(self):
        p=profile();p['opcodes']['7']['kind']='arbitrary_code'
        with self.assertRaisesRegex(ReconstructionError,'semantic kind'):
            reconstruct(parsed(fn([ins(9,b=1)])),p)


if __name__ == '__main__':
    unittest.main()
