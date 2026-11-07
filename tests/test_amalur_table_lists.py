"""Native-derived LEN, field, constructor, and SETLIST obligations.

Run in project-local Lua 5.1 on Windows. Tests establish guarded generated-code
behavior; they do not reproduce native allocation, GC, or Havok table internals.
"""
import json
import os
from pathlib import Path
import unittest

import test_amalur_loops_openlists as base
from lupa.lua51 import LuaError
from amalur_reconstruct import ReconstructionError

ins, fn, branch = base.ins, base.fn, base.branch


def string(value):
    return {'type': 'string', 'value': {'bytes_hex': value.encode().hex()}}


class TableListRuntimeTests(unittest.TestCase):
    lift = base.LoopOpenListRuntimeTests.lift
    build = base.LoopOpenListRuntimeTests.build
    packed = base.LoopOpenListRuntimeTests.packed
    assert_unresolved = base.LoopOpenListRuntimeTests.assert_unresolved

    @classmethod
    def setUpClass(cls):
        path = Path(os.environ.get('AMALUR_NATIVE_PROFILE', base.ROOT / 'outputs' / 'native-script-profile.json'))
        cls.profile = json.loads(path.read_text(encoding='utf-8-sig'))

    def test_length_uses_string_bytes_including_nul_and_utf8(self):
        lua, run = self.build(fn([ins(49, a=1, b=0), ins(9, a=1, b=2)], params=1, stack=2))
        for value, length in [('', 0), ('abc', 3), ('a\0b', 3), ('é', 2), ('😀', 4)]:
            with self.subTest(value=value):
                self.assertEqual(run(value), length)
        self.assertEqual(lua.eval('function(f) return f(string.char(0,255,65)) end')(run), 3)

    def test_length_dense_sequence_counts_false_and_ignores_nonsequence_keys(self):
        lua, run = self.build(fn([ins(49, a=1, b=0), ins(9, a=1, b=2)], params=1, stack=2))
        self.assertEqual(run(lua.eval('{}')), 0)
        self.assertEqual(run(lua.eval("{'a', false, 'c', label='metadata', [0]='zero', [-1]='negative'}")), 3)

    def test_length_rejects_holes_outliers_metatables_and_other_types(self):
        lua, run = self.build(fn([ins(49, a=1, b=0), ins(9, a=1, b=2)], params=1, stack=2))
        for expression in ["{[1]='a',[3]='c'}", "{[1]='a',[999]='far'}", "{[2]='b'}",
                           "setmetatable({'a'}, {})", '42', 'false']:
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(LuaError, 'Amalur'):
                    run(lua.eval(expression))

    def test_length_does_not_establish_hidden_cached_value(self):
        self.assert_unresolved(fn([ins(49, a=1, b=0), ins(67, a=2, b=1, c=0),
                                   ins(70), ins(70), ins(9, a=2, b=2)],
                                  params=1, stack=3, constants=[string('field')]))

    def test_ordinary_getfield_establishes_following_cached_field_value(self):
        lua, run = self.build(fn([ins(0, a=1, b=0, c=0), ins(70), ins(70),
                                 ins(67, a=2, b=1, c=1), ins(70), ins(70), ins(9, a=2, b=2)],
                                params=1, stack=3, constants=[string('outer'), string('value')]))
        self.assertEqual(run(lua.eval('{outer={value=37}}')), 37)

    def test_ordinary_getfield_requires_plain_table_domain(self):
        lua, run = self.build(fn([ins(0, a=1, b=0, c=0), ins(70), ins(70), ins(9, a=1, b=2)],
                                params=1, stack=2, constants=[string('field')]))
        self.assertEqual(run(lua.eval('{field=19}')), 19)
        self.assertIsNone(run(lua.table()))
        with self.assertRaisesRegex(LuaError, 'Amalur'):
            run(lua.eval("setmetatable({}, {__index=function() return 'invented' end})"))

    def test_ordinary_getfield_high_c_bit_is_not_misread_as_large_constant_index(self):
        constants = [string('unused') for _ in range(258)]
        constants[1] = string('native-low-eight-bit-key')
        constants[257] = string('wrong-nine-bit-key')
        self.assert_unresolved(fn([ins(0, a=1, b=0, c=257), ins(70), ins(70), ins(9, a=1, b=2)],
                                  params=1, stack=2, constants=constants))

    def test_branch_cannot_enter_getfield_cache_payload(self):
        with self.assertRaisesRegex(ReconstructionError, 'inline data'):
            self.lift(fn([branch(28, 0, 2), ins(0, a=1, b=0, c=0), ins(70), ins(70), ins(9, b=1)],
                         params=1, stack=2, constants=[string('field')]))

    def test_nonzero_constructor_hints_still_make_distinct_empty_tables(self):
        for b, c in [(1, 0), (0, 2), (2, 3)]:
            with self.subTest(b=b, c=c):
                lua, run = self.build(fn([ins(46, a=0, b=b, c=c), ins(9, b=2)], stack=1))
                first, second = run(), run()
                self.assertEqual(lua.eval('function(t) local n=0; for k,v in pairs(t) do n=n+1 end; return n end')(first), 0)
                self.assertFalse(lua.eval('rawequal')(first, second))

    def test_nonzero_constructor_establishes_cached_table_for_field_write(self):
        lua, run = self.build(fn([ins(46, a=0, b=2, c=2), ins(68, a=0, b=0, c=257), ins(9, b=2)],
                                stack=1, constants=[string('key'), string('value')]))
        self.assertEqual(run()['key'], 'value')

    def test_constructor_capacity_domain_accepts_112_and_rejects_113(self):
        for b, c in [(112, 0), (0, 112)]:
            with self.subTest(b=b, c=c):
                lua, run = self.build(fn([ins(46, a=0, b=b, c=c), ins(9, b=2)], stack=1))
                self.assertEqual(lua.eval('function(t) return next(t) == nil end')(run()), True)
        for b, c in [(113, 0), (0, 113)]:
            with self.subTest(b=b, c=c):
                self.assert_unresolved(fn([ins(46, a=0, b=b, c=c), ins(9, b=2)], stack=1))

    def test_setlist_fixed_values_overwrite_only_selected_indices(self):
        lua, run = self.build(fn([ins(58, a=0, b=3, c=1), ins(9, a=0, b=2)], params=4, stack=4))
        table = lua.eval("{[1]='old1',[2]='old2',[3]='old3',[4]='keep'}")
        returned = run(table, 7, None, 9)
        self.assertTrue(lua.eval('rawequal')(table, returned))
        self.assertEqual([table[i] for i in range(1, 5)], [7, None, 9, 'keep'])

    def test_setlist_fixed_block_uses_50_element_stride_and_full_c9(self):
        for block in [2, 257]:
            with self.subTest(block=block):
                lua, run = self.build(fn([ins(58, a=0, b=1, c=block), ins(9, a=0, b=2)], params=2, stack=2))
                table = lua.eval("{[1]='keep'}")
                run(table, 'written')
                self.assertEqual(table[(block - 1) * 50 + 1], 'written')
                self.assertEqual(table[1], 'keep')

    def test_setlist_extended_block_consumes_data_word(self):
        lua, run = self.build(fn([ins(58, a=0, b=1, c=0), ins(70, bx=513), ins(9, a=0, b=2)],
                                params=2, stack=2))
        table = lua.table()
        run(table, 42)
        self.assertEqual(table[25601], 42)

    def test_setlist_extension_zero_block_and_missing_data_are_rejected(self):
        self.assert_unresolved(fn([ins(58, a=0, b=1, c=0), ins(70, bx=0), ins(9, b=1)], params=2, stack=2))
        with self.assertRaisesRegex(ReconstructionError, 'DATA|data'):
            self.lift(fn([ins(58, a=0, b=1, c=0), ins(9, b=1)], params=2, stack=2))

    def test_setlist_open_values_preserve_nil_count_and_existing_outside_entries(self):
        lua, run = self.build(fn([ins(61, a=1, b=0), ins(58, a=0, b=0, c=1), ins(9, a=0, b=2)],
                                params=1, stack=3, varargs=True))
        table = lua.eval("{[1]='old1',[2]='old2',[3]='old3',[4]='old4',[5]='keep'}")
        run(table, 'new1', None, 'new3', None)
        self.assertEqual([table[i] for i in range(1, 6)], ['new1', None, 'new3', None, 'keep'])
        run(table)
        self.assertEqual([table[i] for i in range(1, 6)], ['new1', None, 'new3', None, 'keep'])

    def test_setlist_open_reset_nil_fills_remaining_register_window(self):
        lua, run = self.build(fn([ins(61, a=1, b=0), ins(58, a=0, b=0, c=1), ins(9, a=1, b=4)],
                                params=1, stack=4, varargs=True))
        self.assertEqual(self.packed(lua, run, lua.table()), [None, None, None])
        self.assertEqual(self.packed(lua, run, lua.table(), 7), [7, None, None])
        self.assertEqual(self.packed(lua, run, lua.table(), 7, None, 9), [7, None, 9])

    def test_setlist_fixed_with_pending_open_top_also_resets_and_nil_fills(self):
        lua, run = self.build(fn([ins(61, a=2, b=0), ins(58, a=0, b=1, c=1), ins(9, a=1, b=4)],
                                params=2, stack=4, varargs=True))
        table = lua.table()
        self.assertEqual(self.packed(lua, run, table, 'fixed', 7), ['fixed', 7, None])
        self.assertEqual(table[1], 'fixed')

    def test_setlist_does_not_leave_dynamic_top_provenance(self):
        self.assert_unresolved(fn([ins(61, a=1, b=0), ins(58, a=0, b=0, c=1), ins(9, b=0)],
                                  params=1, stack=3, varargs=True))

    def test_setlist_rejects_metatable_backed_tables(self):
        lua, run = self.build(fn([ins(58, a=0, b=1, c=1), ins(9, b=1)], params=2, stack=2))
        with self.assertRaisesRegex(LuaError, 'Amalur'):
            run(lua.eval("setmetatable({}, {__newindex=function() error('metamethod must not run') end})"), 7)


if __name__ == '__main__':
    unittest.main(verbosity=2)
