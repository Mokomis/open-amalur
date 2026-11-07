"""Windows Lua 5.1 checks for independently traced native integer/table paths."""
import json
import os
from pathlib import Path
import random
import unittest

import test_amalur_loops_openlists as base
from lupa.lua51 import LuaError

ins, fn = base.ins, base.fn

def number(value):
    return {'type':'number','raw_hex':int(value).to_bytes(4,'big',signed=True).hex()}

def string(value):
    return {'type':'string','value':{'bytes_hex':value.encode().hex()}}

def wrap(value):
    value &= 0xffffffff
    return value if value < 0x80000000 else value-0x100000000

class NativeOperationRuntimeTests(unittest.TestCase):
    lift = base.LoopOpenListRuntimeTests.lift
    build = base.LoopOpenListRuntimeTests.build
    packed = base.LoopOpenListRuntimeTests.packed
    assert_unresolved = base.LoopOpenListRuntimeTests.assert_unresolved

    @classmethod
    def setUpClass(cls):
        path=Path(os.environ.get('AMALUR_NATIVE_PROFILE',base.ROOT/'outputs/native-script-profile.json'))
        cls.profile=json.loads(path.read_text(encoding='utf-8-sig'))

    def binary(self,opcode,destination=2):
        return fn([ins(opcode,a=destination,b=0,c=1),ins(9,a=destination,b=2)],params=2,stack=3)

    def test_add_signed_wrap_boundaries(self):
        _, run=self.build(self.binary(34))
        for left,right in [(2147483647,1),(-2147483648,-1),(-2147483648,-2147483648),
                           (2147483647,2147483647),(-7,3),(0,0)]:
            with self.subTest(left=left,right=right):self.assertEqual(run(left,right),wrap(left+right))

    def test_subtract_signed_wrap_and_operand_order(self):
        _, run=self.build(self.binary(36))
        for left,right in [(-2147483648,1),(2147483647,-1),(7,-3),(-3,7),(-2147483648,2147483647)]:
            with self.subTest(left=left,right=right):self.assertEqual(run(left,right),wrap(left-right))

    def test_multiply_keeps_low_bits_beyond_lua_double_precision(self):
        _, run=self.build(self.binary(38))
        values=[-2147483648,-2147483647,-65537,-65536,-1,0,1,65535,65536,65537,2147483646,2147483647]
        for left in values:
            for right in values:
                with self.subTest(left=left,right=right):self.assertEqual(run(left,right),wrap(left*right))

    def test_multiply_deterministic_full_width_reference(self):
        _, run=self.build(self.binary(38));rng=random.Random(20261030)
        for _ in range(128):
            left=rng.randrange(-2147483648,2147483648);right=rng.randrange(-2147483648,2147483648)
            self.assertEqual(run(left,right),wrap(left*right),(left,right))

    def test_modulo_uses_dividend_sign_not_lua_floor_remainder(self):
        _, run=self.build(self.binary(42))
        for left,right in [(7,3),(-7,3),(7,-3),(-7,-3),(-1,2),(1,-2),(0,-7),(-2147483648,3)]:
            expected=abs(left)%abs(right)
            if left<0:expected=-expected
            with self.subTest(left=left,right=right):self.assertEqual(run(left,right),expected)

    def test_modulo_division_traps_are_explicit(self):
        _, run=self.build(self.binary(42))
        for left,right in [(1,0),(0,0),(-2147483648,-1)]:
            with self.subTest(left=left,right=right):
                with self.assertRaisesRegex(LuaError,'Amalur|integer|division'):run(left,right)

    def test_power_native_negative_zero_and_positive_exponents(self):
        _, run=self.build(self.binary(44))
        for left,right in [(0,-1),(2,-1),(-2,-3),(0,0),(123,0),(-2,3),(-2,4),
                           (65537,2),(2147483647,2),(3,31),(2,32),(7,2147483647)]:
            expected=0 if right<0 else wrap(pow(left,right,0x100000000))
            with self.subTest(left=left,right=right):self.assertEqual(run(left,right),expected)

    def test_unary_negation_wraps_minimum_integer(self):
        _, run=self.build(fn([ins(47,a=1,b=0),ins(9,a=1,b=2)],params=1,stack=2))
        for value in [-2147483648,-2147483647,-1,0,1,2147483647]:
            with self.subTest(value=value):self.assertEqual(run(value),wrap(-value))

    def test_unary_negation_guard_alias_and_zero(self):
        lua,run=self.build(fn([ins(47,a=0,b=0),ins(9,a=0,b=2)],params=1,stack=1))
        for value in [None,True,'1',0.25,2147483648,float('inf')]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(LuaError,'Amalur|integer'):run(value)
        self.assertEqual(run(17),-17)
        self.assertTrue(lua.eval('function(f) return 1/f(0)==math.huge end')(run))

    def test_arithmetic_snapshots_inputs_before_destination_alias(self):
        for op,expected in [(34,10),(36,4),(38,21),(42,1),(44,343)]:
            for destination in [0,1]:
                with self.subTest(op=op,destination=destination):
                    _,run=self.build(self.binary(op,destination));self.assertEqual(run(7,3),expected)

    def test_arithmetic_constant_and_register_selectors(self):
        for op,expected in [(34,10),(36,4),(38,21),(42,1),(44,343)]:
            for body,args in [
                (fn([ins(op+1,a=1,b=0,c=0),ins(9,a=1,b=2)],params=1,stack=2,constants=[number(7)]),(3,)),
                (fn([ins(op,a=1,b=0,c=256),ins(9,a=1,b=2)],params=1,stack=2,constants=[number(3)]),(7,)),
                (fn([ins(op+1,a=0,b=0,c=257),ins(9,a=0,b=2)],stack=1,constants=[number(7),number(3)]),()),
            ]:
                with self.subTest(op=op,args=args):
                    _,run=self.build(body);self.assertEqual(run(*args),expected)

    def test_arithmetic_rejects_noninteger_and_metamethod_domains(self):
        for op in [34,36,38,42,44]:
            lua,run=self.build(self.binary(op))
            for value in [True,None,'7',0.5,2147483648,-2147483649,float('nan'),float('inf'),
                          lua.eval("setmetatable({}, {__add=function() error('wrong path') end})")]:
                with self.subTest(op=op,value=str(value)):
                    with self.assertRaisesRegex(LuaError,'Amalur|integer'):run(value,2)
                    with self.assertRaisesRegex(LuaError,'Amalur|integer'):run(2,value)

    def test_integer_zero_is_canonical_after_arithmetic(self):
        for op,args in [(34,(-0.0,0)),(36,(-0.0,0)),(38,(-1,0)),(42,(-6,3)),(44,(2,-3))]:
            lua,run=self.build(self.binary(op))
            observe=lua.eval('function(f,a,b) local v=f(a,b); return v==0 and 1/v==math.huge end')
            with self.subTest(op=op):self.assertTrue(observe(run,*args))

    def test_arithmetic_does_not_falsely_produce_hidden_cache(self):
        for op in [34,36,38,42,44]:
            with self.subTest(op=op):
                self.assert_unresolved(fn([ins(op,a=2,b=0,c=1),ins(67,a=3,b=2,c=0),ins(70),ins(70),
                                           ins(9,a=3,b=2)],params=2,stack=4,constants=[string('field')]))

    def test_self_preserves_receiver_and_looks_up_method(self):
        lua,run=self.build(fn([ins(8,a=0,b=1,c=256),ins(9,a=0,b=3)],params=2,stack=2,constants=[string('method')]))
        receiver=lua.eval('{method=function() return 7 end}')
        result=lua.eval('function(f,t) local method,receiver=f(nil,t); return method==t.method and receiver==t end')
        self.assertTrue(result(run,receiver))

    def test_self_snapshots_key_before_receiver_slot_overwrite(self):
        lua,run=self.build(fn([ins(8,a=0,b=0,c=1),ins(9,a=0,b=3)],params=2,stack=2))
        table=lua.eval('{method=function() return 7 end}')
        check=lua.eval('function(f,t) local method,receiver=f(t,"method"); return method==t.method and receiver==t end')
        self.assertTrue(check(run,table))

    def test_self_establishes_immediate_cached_callable(self):
        lua,run=self.build(fn([ins(8,a=0,b=0,c=256),ins(63,a=0,b=2,c=2),ins(9,a=0,b=2)],
                               params=1,stack=2,constants=[string('method')]))
        receiver=lua.eval('{mark=17,method=function(self) return self.mark end}')
        self.assertEqual(run(receiver),17)

    def test_self_missing_method_still_copies_receiver(self):
        lua,run=self.build(fn([ins(8,a=0,b=0,c=256),ins(9,a=0,b=3)],params=1,stack=2,constants=[string('missing')]))
        check=lua.eval('function(f,t) local method,receiver=f(t); return method==nil and receiver==t end')
        self.assertTrue(check(run,lua.table()))

    def test_self_rejects_custom_table_and_nonstring_key_domains(self):
        lua,run=self.build(fn([ins(8,a=2,b=0,c=1),ins(9,a=2,b=3)],params=2,stack=4))
        for table,key in [(lua.eval('setmetatable({}, {})'),'method'),(lua.table(),1),(None,'method')]:
            with self.subTest(key=key):
                with self.assertRaisesRegex(LuaError,'Amalur|table|SELF'):run(table,key)

    def test_settable_string_register_and_constant_keys(self):
        for body,args in [
            (fn([ins(16,a=0,b=1,c=2),ins(9,a=0,b=2)],params=3,stack=3),('key',7)),
            (fn([ins(17,a=0,b=0,c=256+1),ins(9,a=0,b=2)],params=1,stack=1,constants=[string('key'),number(7)]),()),
        ]:
            lua,run=self.build(body);table=lua.table();result=run(table,*args)
            self.assertEqual(result['key'],7);self.assertEqual(table['key'],7)

    def test_settable_numeric_and_generic_keys(self):
        for op in [18,20]:
            lua,run=self.build(fn([ins(op,a=0,b=1,c=2),ins(9,a=0,b=2)],params=3,stack=3))
            for key in [-2147483648,-1,0,1,2147483647]:
                table=lua.table();run(table,key,'value');self.assertEqual(table[key],'value')

    def test_settable_can_store_false_nil_and_self_reference(self):
        lua,run=self.build(fn([ins(16,a=0,b=1,c=2),ins(9,a=0,b=2)],params=3,stack=3))
        table=lua.eval('{key="old"}')
        run(table,'key',False);self.assertFalse(table['key'])
        run(table,'key',None);self.assertIsNone(table['key'])
        run(table,'key',table)
        self.assertTrue(lua.eval('function(t) return t.key==t end')(table))

    def test_settable_rejects_metatables_and_unmodeled_keys(self):
        lua,run=self.build(fn([ins(20,a=0,b=1,c=2),ins(9,b=1)],params=3,stack=3))
        for table,key in [(lua.eval('setmetatable({}, {})'),'key'),(lua.table(),None),(lua.table(),0.5),
                          (lua.table(),2147483648)]:
            with self.subTest(key=key):
                with self.assertRaisesRegex(LuaError,'Amalur|table'):run(table,key,7)

    def test_settable_does_not_establish_hidden_cache(self):
        self.assert_unresolved(fn([ins(16,a=0,b=1,c=2),ins(67,a=3,b=0,c=0),ins(70),ins(70),
                                   ins(9,a=3,b=2)],params=3,stack=4,constants=[string('field')]))

    def test_gettable_numeric_and_generic_own_two_data_words(self):
        for op in [11,12]:
            lua,run=self.build(fn([ins(op,a=2,b=0,c=1),ins(70),ins(70),ins(9,a=2,b=2)],params=2,stack=3))
            table=lua.eval('{[3]="three", key="text"}')
            self.assertEqual(run(table,3),'three')
            self.assertEqual(run(table,'key'),'text')

    def test_typed_settable_fallback_preserves_constant_key_flag(self):
        for op,key,constant in [(17,3,number(3)),(19,'key',string('key'))]:
            lua,run=self.build(fn([ins(op,a=0,b=0,c=1),ins(9,a=0,b=2)],params=2,stack=2,
                                   constants=[constant]))
            table=lua.table();run(table,'value');self.assertEqual(table[key],'value')

    def test_concat_preserves_forward_order_and_embedded_nul(self):
        _,run=self.build(fn([ins(54,a=3,b=0,c=2),ins(9,a=3,b=2)],params=3,stack=4))
        self.assertEqual(run('first','middle','last'),'firstmiddlelast')
        self.assertEqual(run('a\0b','\0','c\0'),'a\0b\0c\0')
        self.assertEqual(run('','',''),'')

    def test_concat_reads_exact_inclusive_span(self):
        _,run=self.build(fn([ins(54,a=4,b=1,c=2),ins(9,a=4,b=2)],params=4,stack=5))
        self.assertEqual(run('outside-left','left','right','outside-right'),'leftright')

    def test_concat_destination_may_alias_span(self):
        for dest in [0,1,2]:
            with self.subTest(dest=dest):
                _,run=self.build(fn([ins(54,a=dest,b=0,c=2),ins(9,a=dest,b=2)],params=3,stack=3))
                self.assertEqual(run('a','b','c'),'abc')

    def test_concat_leaves_original_operand_cells_unchanged(self):
        lua,run=self.build(fn([ins(54,a=3,b=0,c=2),ins(9,a=0,b=5)],params=3,stack=4))
        self.assertEqual(self.packed(lua,run,'a','b','c'),['a','b','c','abc'])

    def test_concat_formats_signed_int32_in_plain_decimal(self):
        _,run=self.build(fn([ins(54,a=3,b=0,c=2),ins(9,a=3,b=2)],params=3,stack=4))
        for value in [-2147483648,-2147483647,-1000000000,-1,0,1,1000000000,2147483646,2147483647]:
            with self.subTest(value=value):self.assertEqual(run('[',value,']'),'['+str(value)+']')
        self.assertEqual(run(-2147483648,':',2147483647),'-2147483648:2147483647')
        self.assertEqual(run(-0.0,0,-0.0),'000')

    def test_concat_numeric_conversion_does_not_modify_original_cells(self):
        lua,run=self.build(fn([ins(54,a=3,b=0,c=2),ins(9,a=0,b=5)],params=3,stack=4))
        self.assertEqual(self.packed(lua,run,7,':',-19),[7,':',-19,'7:-19'])

    def test_concat_numeric_domain_rejects_noninteger_and_out_of_range_values(self):
        _,run=self.build(fn([ins(54,a=2,b=0,c=1),ins(9,a=2,b=2)],params=2,stack=3))
        for value in [0.5,2147483648,-2147483649,float('nan'),float('inf'),-float('inf')]:
            with self.subTest(value=value):
                with self.assertRaisesRegex(LuaError,'Amalur|integer'):run(value,'x')
                with self.assertRaisesRegex(LuaError,'Amalur|integer'):run('x',value)

    def test_concat_decimal_rendering_is_independent_of_custom_tostring(self):
        lua,run=self.build(fn([ins(54,a=2,b=0,c=1),ins(9,a=2,b=2)],params=2,stack=3))
        lua.execute('tostring=function() return "incorrect" end')
        self.assertEqual(run('number=',2147483647),'number=2147483647')

    def test_concat_single_operand_is_identity_without_conversion(self):
        lua,run=self.build(fn([ins(54,a=1,b=0,c=0),ins(9,a=1,b=2)],params=1,stack=2))
        for value in [None,False,True,17,'text']:
            with self.subTest(value=value):self.assertEqual(run(value),value)
        table=lua.eval('setmetatable({}, {__concat=function() error("must not run") end})')
        self.assertTrue(lua.eval('function(f,t) return f(t)==t end')(run,table))

    def test_concat_rejects_nonprimitive_pair_before_metamethod(self):
        lua,run=self.build(fn([ins(54,a=2,b=0,c=1),ins(9,a=2,b=2)],params=2,stack=3))
        table=lua.eval('setmetatable({}, {__concat=function() error("wrong metamethod path") end})')
        for value in [None,False,True,table]:
            with self.subTest(value=str(value)):
                with self.assertRaisesRegex(LuaError,'Amalur|concatenation'):run(value,'suffix')
                with self.assertRaisesRegex(LuaError,'Amalur|concatenation'):run('prefix',value)

    def test_concat_dynamic_open_top_is_conservatively_unresolved(self):
        self.assert_unresolved(fn([ins(61,a=3,b=0),ins(54,a=0,b=0,c=2),ins(9,a=0,b=2)],
                                   params=3,stack=4,varargs=True))

    def test_concat_rejects_reversed_and_high_flag_spans(self):
        for b,c in [(2,0),(0,257)]:
            with self.subTest(b=b,c=c):
                body=fn([ins(54,a=2,b=b,c=c),ins(9,a=2,b=2)],params=2,stack=3)
                try:
                    ir,source=self.lift(body)
                except ValueError:
                    continue  # Structural range rejection is also fail-closed.
                self.assertFalse(ir['root_function']['body_emittable'])
                self.assertIn('UNRESOLVED',source)

    def test_concat_does_not_establish_hidden_cache(self):
        self.assert_unresolved(fn([ins(54,a=2,b=0,c=1),ins(67,a=3,b=2,c=0),ins(70),ins(70),
                                   ins(9,a=3,b=2)],params=2,stack=4,constants=[string('field')]))

if __name__=='__main__':unittest.main(verbosity=2)
