"""Large dispatcher and native flags-3 variadic regression obligations."""
import json
import os
from pathlib import Path
import unittest

import test_amalur_loops_openlists as base
import test_amalur_real_loops_openlists as real
from amalur_reconstruct import emit_function
from lupa.lua51 import LuaRuntime

ins, fn, branch = base.ins, base.fn, base.branch


def string(value):
    return {'type': 'string', 'value': {'bytes_hex': value.encode().hex()}}


def number(value):
    return {'type': 'number', 'raw_hex': int(value).to_bytes(4, 'big', signed=True).hex()}


class LargeVariadicRuntimeTests(unittest.TestCase):
    lift = base.LoopOpenListRuntimeTests.lift
    packed = base.LoopOpenListRuntimeTests.packed
    assert_unresolved = base.LoopOpenListRuntimeTests.assert_unresolved

    @classmethod
    def setUpClass(cls):
        path = Path(os.environ.get('AMALUR_NATIVE_PROFILE', base.ROOT / 'outputs' / 'native-script-profile.json'))
        cls.profile = json.loads(path.read_text(encoding='utf-8-sig'))

    def build(self, body, large=False):
        ir, _ = self.lift(body)
        self.assertTrue(ir['root_function']['body_emittable'], json.dumps(ir['root_function']['unknowns'], indent=2))
        source = ('local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable\nreturn '
                  + '\n'.join(emit_function(ir['root_function'])))
        if large:
            self.assertIn('local function __dispatch', source)
        lua = LuaRuntime(unpack_returned_tuples=True, register_eval=False, register_builtins=False)
        lua.execute("debug.sethook(function() error('large fixture instruction budget exceeded') end, '', 2000000)")
        lua.execute('io=nil; os=nil; python=nil; dofile=nil; loadfile=nil; require=nil; debug=nil')
        return lua, lua.execute(source)

    def test_large_function_compiles_and_preserves_nil_bearing_return_count(self):
        body = fn([ins(7, a=0, b=0) for _ in range(1001)] + [ins(9, a=0, b=4)], params=3, stack=3)
        lua, run = self.build(body, large=True)
        self.assertEqual(self.packed(lua, run, None, 7, None), [None, 7, None])

    def test_large_function_preserves_zero_return_values(self):
        body = fn([ins(7, a=0, b=0) for _ in range(1001)] + [ins(9, b=1)], params=1, stack=1)
        lua, run = self.build(body, large=True)
        self.assertEqual(self.packed(lua, run, 'unused'), [])

    def test_large_dispatcher_crosses_leaf_boundaries_and_backward_edge(self):
        code = [ins(13, a=1, b=1)] + [ins(7, a=0, b=0) for _ in range(1001)]
        test_pc = len(code)
        code += [ins(1, a=1, c=0), branch(28, test_pc + 1, test_pc + 4),
                 ins(13, a=1, b=0), branch(28, test_pc + 3, 1), ins(9, a=0, b=2)]
        lua, run = self.build(fn(code, params=1, stack=2), large=True)
        self.assertEqual(self.packed(lua, run, 'crossed twice'), ['crossed twice'])

    def test_large_dispatcher_preserves_captured_cell_mutation(self):
        child = fn([ins(32, a=0, b=0), ins(9, a=0, b=2)], stack=1)
        child['upvalue_count'] = 1
        code = [ins(60, a=1, bx=0), ins(70, a=1, bx=0)]
        code += [ins(7, a=0, b=0) for _ in range(1001)]
        code += [ins(25, a=0, bx=0), ins(9, a=1, b=2)]
        body = fn(code, params=1, stack=2, constants=[number(42)])
        body['children'] = [child]
        _, run = self.build(body, large=True)
        getter = run(7)
        self.assertEqual(getter(), 42)

    def test_large_dispatcher_preserves_module_environment_and_nested_function(self):
        nil = {'type': 'nil'}
        constants = [string('module'), nil, nil, string('large_dispatch_fixture'),
                     string('package'), nil, nil, string('seeall'), number(123), string('published'), nil, nil]
        code = [ins(85, a=0, bx=0), ins(70, bx=1), ins(25, a=1, bx=3),
                ins(85, a=2, bx=4), ins(70, bx=5), ins(67, a=2, b=2, c=7), ins(70), ins(70),
                ins(2, a=0, b=3, c=1), ins(25, a=0, bx=8)]
        code += [ins(7, a=0, b=0) for _ in range(1001)]
        code += [ins(27, a=0, bx=9), ins(85, a=0, bx=9), ins(70, bx=10),
                 ins(60, a=1, bx=0), ins(9, a=0, b=3)]
        child = fn([ins(85, a=0, bx=0), ins(70, bx=1), ins(9, a=0, b=2)],
                   stack=1, constants=[string('published'), nil, nil])
        body = fn(code, stack=3, constants=constants)
        body['children'] = [child]
        lua, run = self.build(body, large=True)
        value, callback = run()
        self.assertEqual(value, 123)
        self.assertEqual(callback(), 123)
        module = lua.globals().large_dispatch_fixture
        self.assertEqual(module.published, 123)
        self.assertTrue(lua.eval('rawequal')(lua.eval('getfenv')(run), module))
        self.assertTrue(lua.eval('rawequal')(lua.eval('getfenv')(callback), module))
        self.assertIsNone(lua.globals().published)

    def test_large_variadic_dispatcher_returns_all_values_without_losing_nil(self):
        code = [ins(7, a=0, b=0) for _ in range(1001)]
        code += [ins(61, a=1, b=0), ins(9, a=0, b=0)]
        body = fn(code, params=1, stack=2, varargs=True)
        body['vararg_flags'] = 3
        lua, run = self.build(body, large=True)
        self.assertEqual(self.packed(lua, run, 'fixed', None, 8, None), ['fixed', None, 8, None])
        self.assertEqual(self.packed(lua, run, 'fixed'), ['fixed'])

    def test_flags_three_forward_variadic_values_with_fixed_parameter(self):
        body = fn([ins(61, a=1, b=0), ins(9, a=0, b=0)], params=1, stack=2, varargs=True)
        body['vararg_flags'] = 3
        lua, run = self.build(body)
        self.assertEqual(self.packed(lua, run, 'fixed', None, 8, None), ['fixed', None, 8, None])

    def test_variadic_entry_nil_slot_does_not_expose_first_extra_argument(self):
        for flags in [2, 3]:
            with self.subTest(flags=flags):
                body = fn([ins(9, a=1, b=2)], params=1, stack=2, varargs=True)
                body['vararg_flags'] = flags
                lua, run = self.build(body)
                self.assertEqual(self.packed(lua, run, 'fixed', 99, 100), [None])

    def test_legacy_argtable_flag_seven_preserves_original_varargs(self):
        body = fn([ins(61, a=1, b=0), ins(9, a=0, b=0)], params=1, stack=2, varargs=True)
        body['vararg_flags'] = 7
        lua,run=self.build(body)
        self.assertEqual(self.packed(lua,run,'fixed',None,8,None),['fixed',None,8,None])


class RealVariadicRuntimeTests(unittest.TestCase):
    build = real.RealLoopOpenListRuntimeTests.build

    def test_real_faction_wrappers_forward_exact_variadic_lists(self):
        sample_directory = Path(os.environ.get('AMALUR_FULL_SCRIPT_SAMPLES',
                                               base.ROOT / 'work' / 'initial-script-corpus-v04'))
        words = ['aa000001', '8c000114', '32000302', '7a000003', '04000101', '12020000']
        for path, relation in [('0/1', 'Hostile'), ('0/2', 'Neutral'), ('0/3', 'Friendly'), ('0/4', 'Ally')]:
            with self.subTest(path=path, relation=relation):
                lua, run = self.build('13158.lua_bxml',
                                      '6827ed79894cdaf528a544613d647a402e3436134c6b1afc680e874fe2ab18a5',
                                      path, words, sample_directory=sample_directory)
                lua.execute('''
                  events = {}
                  modify_faction_relation = function(...)
                    events[#events+1] = {n=select('#', ...), ...}
                  end
                ''')
                invoke = lua.eval("function(f, ...) return select('#', f(...)) end")
                for args in [(), ('faction-A',), ('faction-A', None, 'faction-B', None)]:
                    self.assertEqual(invoke(run, *args), 0)
                    event = lua.globals().events[len(lua.globals().events)]
                    self.assertEqual([event[i] for i in range(1, event.n + 1)], [relation, *args])


if __name__ == '__main__':
    unittest.main(verbosity=2)
