"""Five bounded table/cached-upvalue runtime obligations for generated Lua 5.1.

No Havok or game code is executed. Reuses fixture construction and isolated
runtime helpers, but does not inherit or duplicate the earlier test methods.
"""
import json
import os
from pathlib import Path
import unittest

import test_amalur_lua_runtime as base
from lupa.lua51 import LuaError

ins, fn, number, string, capture = base.ins, base.fn, base.number, base.string, base.capture


class GeneratedTableRuntimeTests(unittest.TestCase):
    runtime = base.GeneratedLuaRuntimeTests.runtime
    build = base.GeneratedLuaRuntimeTests.build

    @classmethod
    def setUpClass(cls):
        path = Path(os.environ.get('AMALUR_NATIVE_PROFILE', base.ROOT / 'outputs' / 'native-script-profile.json'))
        cls.profile = json.loads(path.read_text(encoding='utf-8-sig'))

    def test_fresh_table_cached_field_write_and_table_read(self):
        body = fn([ins(46, a=0), ins(68, a=0, b=0, c=257),
                   ins(10, a=1, b=0, c=256), ins(70), ins(70), ins(9, a=1, b=2)],
                  [string('answer'), number(37)], stack=2)
        _, run = self.build(body)
        self.assertEqual(run(), 37)

    def test_regular_setfield_mutates_argument_using_constant_value(self):
        body = fn([ins(15, a=0, b=0, c=257), ins(9, a=0, b=2)],
                  [string('tag'), string('marker')], params=1, stack=1)
        lua, run = self.build(body)
        table = lua.table()
        returned = run(table)
        self.assertTrue(lua.eval('rawequal')(table, returned))
        self.assertEqual(table['tag'], 'marker')

    def test_gettable_string_and_signed_integer_keys(self):
        body = fn([ins(10, a=2, b=0, c=1), ins(70), ins(70), ins(9, a=2, b=2)], params=2, stack=3)
        lua, run = self.build(body)
        table = lua.eval("{label='named',[-2147483648]='min',[2147483647]='max',[0]='zero'}")
        for key, value in [('label', 'named'), (-2147483648, 'min'), (2147483647, 'max'), (0, 'zero'), ('missing', None)]:
            with self.subTest(key=key):
                self.assertEqual(run(table, key), value)

    def test_gettable_rejects_metatables_and_unmodeled_key_domains(self):
        body = fn([ins(10, a=2, b=0, c=1), ins(70), ins(70), ins(9, a=2, b=2)], params=2, stack=3)
        lua, run = self.build(body)
        ordinary = lua.table()
        metatable = lua.eval("setmetatable({}, {__index=function() return 'invented' end})")
        for table, key in [(metatable, 'x'), (17, 'x'), (ordinary, 0.5),
                           (ordinary, 2147483648), (ordinary, -2147483649),
                           (ordinary, True), (ordinary, None), (ordinary, lua.table())]:
            with self.subTest(key_type=type(key).__name__, key=str(key)):
                with self.assertRaisesRegex(LuaError, 'Unmodeled Amalur table(?:-key)? domain'):
                    run(table, key)

    def test_newtable_cached_upvalue_write_is_shared_with_sibling_getter(self):
        make_table = fn([ins(46, a=0), ins(64, a=0, b=0), ins(9, a=0, b=2)], stack=1, upvalues=1)
        root = fn([ins(60, a=1, bx=0), capture(True, 0),
                   ins(60, a=2, bx=1), capture(True, 0), ins(9, a=1, b=3)],
                  children=[base.getter(), make_table], params=1, stack=3)
        lua, make = self.build(root)
        original = lua.eval("{marker='original'}")
        get, replace = make(original)
        self.assertTrue(lua.eval('rawequal')(get(), original))
        fresh = replace()
        self.assertFalse(lua.eval('rawequal')(fresh, original))
        self.assertTrue(lua.eval('rawequal')(get(), fresh))
        fresh['later'] = 42
        self.assertEqual(get()['later'], 42)
        self.assertEqual(original['marker'], 'original')
        self.assertIsNone(original['later'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
