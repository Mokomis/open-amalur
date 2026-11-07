"""Independent generated-Lua behavior fixtures. Run only on the Windows host.

These establish generated Lua 5.1 behavior for synthetic obligations and a
mocked real script. They do not execute the Havok VM or prove game equivalence.
"""
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'python-libs'))
sys.path.insert(0, str(ROOT / 'src'))
from lupa import __version__ as LUPA_VERSION
from lupa.lua51 import LUA_VERSION, LuaRuntime
from amalur_script import decode_instruction
from amalur_reconstruct import reconstruct


def ins(op, a=0, b=0, c=0, bx=None):
    word = (op << 25) | a | (((b << 9) | c) << 8 if bx is None else bx << 8)
    return decode_instruction(word, 0, 0)


def jump(pc, target):
    return ins(28, bx=65535 + target - pc - 1)


def capture(local, index):
    return ins(70, a=1 if local else 0, bx=index)


def number(n):
    return {'type': 'number', 'raw_hex': int(n).to_bytes(4, 'big', signed=True).hex()}


def string(s):
    return {'type': 'string', 'value': {'bytes_hex': s.encode().hex()}}


def fn(code, constants=(), children=(), params=0, stack=8, upvalues=0):
    return {'instructions': [dict(row, pc=i, file_offset=0x100 + i * 4) for i, row in enumerate(code)],
            'constants': list(constants), 'children': list(children), 'parameter_count': params,
            'maximum_stack_size': stack, 'upvalue_count': upvalues, 'vararg_flags': 0}


def getter():
    return fn([ins(32, a=0, b=0), ins(9, a=0, b=2)], stack=1, upvalues=1)


def setter():
    return fn([ins(33, a=0, b=0), ins(9, a=0, b=2)], params=1, stack=1, upvalues=1)


def sibling_factory():
    return fn([ins(60, a=1, bx=0), capture(True, 0),
               ins(60, a=2, bx=1), capture(True, 0), ins(9, a=1, b=3)],
              children=[getter(), setter()], params=1, stack=3)


class GeneratedLuaRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if tuple(LUA_VERSION) != (5, 1):
            raise AssertionError('Runtime fixtures require actual Lua 5.1, got ' + repr(LUA_VERSION))
        profile_path = Path(os.environ.get('AMALUR_NATIVE_PROFILE', ROOT / 'outputs' / 'native-script-profile.json'))
        cls.profile = json.loads(profile_path.read_text(encoding='utf-8-sig'))

    def runtime(self):
        lua = LuaRuntime(unpack_returned_tuples=True, register_eval=False, register_builtins=False)
        self.assertEqual(lua.eval('_VERSION'), 'Lua 5.1')
        # An accidental emitter backedge cannot hang the test process indefinitely.
        lua.execute("debug.sethook(function() error('runtime fixture instruction budget exceeded') end, '', 100000)")
        lua.execute('io=nil; os=nil; python=nil; dofile=nil; loadfile=nil; require=nil; debug=nil')
        return lua

    def build(self, function):
        parsed = {'input_sha256': '0' * 64, 'chunk': {'root_function': function}}
        ir, source = reconstruct(parsed, self.profile)
        self.assertEqual(ir['summary']['unresolved_function_bodies'], 0,
                         json.dumps(ir['root_function'].get('unknowns', []), indent=2))
        lua = self.runtime()
        runner = lua.eval('function(...)\n' + source + '\nend')
        return lua, runner

    def test_runtime_is_actual_lua51_and_pinned_lupa(self):
        self.assertEqual(LUPA_VERSION, '2.6')
        self.runtime()

    def test_test_branch_truthiness_and_polarity(self):
        body = fn([ins(1, a=0, c=1), jump(1, 4),
                   ins(25, a=1, bx=0), ins(9, a=1, b=2),
                   ins(25, a=1, bx=1), ins(9, a=1, b=2)],
                  [string('false path'), string('true path')], params=1, stack=2)
        lua, run = self.build(body)
        for value, expected in [(False, 'false path'), (None, 'false path'),
                                (True, 'true path'), (0, 'true path'), ('', 'true path')]:
            with self.subTest(value=value):
                self.assertEqual(run(value), expected)
        self.assertEqual(run(lua.table()), 'true path')

    def test_test_branch_false_selector_reverses_taken_edge(self):
        body = fn([ins(1, a=0, c=0), jump(1, 4),
                   ins(25, a=1, bx=0), ins(9, a=1, b=2),
                   ins(25, a=1, bx=1), ins(9, a=1, b=2)],
                  [string('truthy'), string('falsy')], params=1, stack=2)
        _, run = self.build(body)
        self.assertEqual(run(False), 'falsy')
        self.assertEqual(run(None), 'falsy')
        self.assertEqual(run(0), 'truthy')

    def test_eq_branch_primitive_values_and_types(self):
        body = fn([ins(4, a=1, b=0, c=1), jump(1, 4),
                   ins(25, a=2, bx=0), ins(9, a=2, b=2),
                   ins(25, a=2, bx=1), ins(9, a=2, b=2)],
                  [string('different'), string('equal')], params=2, stack=3)
        _, run = self.build(body)
        for left, right, expected in [(None, None, 'equal'), (False, False, 'equal'),
                                      (17, 17, 'equal'), ('x', 'x', 'equal'),
                                      (17, 18, 'different'), (True, 1, 'different'),
                                      ('17', 17, 'different'), (None, False, 'different')]:
            with self.subTest(left=left, right=right):
                self.assertEqual(run(left, right), expected)

    def test_eq_constant_left_and_inverted_selector(self):
        # EQ_BK's low opcode bit provides the constant-bank bit of B.
        body = fn([ins(5, a=0, b=0, c=0), jump(1, 4),
                   ins(25, a=1, bx=1), ins(9, a=1, b=2),
                   ins(25, a=1, bx=2), ins(9, a=1, b=2)],
                  [number(42), string('equal'), string('different')], params=1, stack=2)
        _, run = self.build(body)
        self.assertEqual(run(42), 'equal')
        self.assertEqual(run(-42), 'different')

    def test_testset_writes_only_on_taken_edge(self):
        body = fn([ins(25, a=1, bx=0), ins(55, a=1, b=0, c=1), jump(2, 4),
                   jump(3, 4), ins(9, a=1, b=2)], [string('fallback')], params=1, stack=2)
        _, run = self.build(body)
        self.assertEqual(run(False), 'fallback')
        self.assertEqual(run(None), 'fallback')
        self.assertEqual(run('chosen'), 'chosen')
        self.assertEqual(run(0), 0)

    def test_backward_jump_loop_reaches_exit(self):
        body = fn([ins(13, a=0, b=1), ins(1, a=0, c=0), jump(2, 5),
                   ins(13, a=0, b=0), jump(4, 1), ins(9, a=0, b=2)], stack=1)
        _, run = self.build(body)
        self.assertIs(run(), False)

    def test_loadbool_skip_has_correct_successor(self):
        body = fn([ins(13, a=0, b=1, c=1), ins(13, a=0, b=0), ins(9, a=0, b=2)], stack=1)
        _, run = self.build(body)
        self.assertIs(run(), True)

    def test_siblings_share_mutable_upvalue_after_parent_return(self):
        _, make = self.build(sibling_factory())
        get, set_value = make(10)
        self.assertEqual(get(), 10)
        self.assertEqual(set_value(21), 21)
        self.assertEqual(get(), 21)
        set_value(None)
        self.assertIsNone(get())

    def test_separate_parent_invocations_do_not_share_cells(self):
        _, make = self.build(sibling_factory())
        get1, set1 = make(10)
        get2, set2 = make(20)
        set1(31)
        self.assertEqual((get1(), get2()), (31, 20))
        set2(42)
        self.assertEqual((get1(), get2()), (31, 42))

    def test_local_capture_observes_later_write_before_return(self):
        body = fn([ins(60, a=1, bx=0), capture(True, 0),
                   ins(25, a=0, bx=0), ins(9, a=1, b=2)],
                  [number(33)], [getter()], params=1, stack=2)
        _, make = self.build(body)
        self.assertEqual(make(10)(), 33)

    def test_grandchild_forwards_parent_upvalue_cell(self):
        middle = fn([ins(60, a=0, bx=0), capture(False, 0), ins(9, a=0, b=2)],
                    children=[getter()], stack=1, upvalues=1)
        root = fn([ins(60, a=1, bx=0), capture(True, 0),
                   ins(60, a=2, bx=1), capture(True, 0), ins(9, a=1, b=3)],
                  children=[middle, setter()], params=1, stack=3)
        _, make = self.build(root)
        make_getter, set_value = make(12)
        get = make_getter()
        self.assertEqual(get(), 12)
        set_value(71)
        self.assertEqual(get(), 71)

    def test_close_detaches_before_register_reuse(self):
        body = fn([ins(60, a=1, bx=0), capture(True, 0), ins(59, a=0),
                   ins(25, a=0, bx=0), ins(60, a=2, bx=0), capture(True, 0),
                   ins(9, a=1, b=3)], [number(99)], [getter()], params=1, stack=3)
        _, make = self.build(body)
        old_get, new_get = make(17)
        self.assertEqual(old_get(), 17)
        self.assertEqual(new_get(), 99)

    def test_close_threshold_keeps_lower_register_capture_open(self):
        two_getter = fn([ins(32, a=0, b=0), ins(32, a=1, b=1), ins(9, a=0, b=3)],
                        stack=2, upvalues=2)
        body = fn([ins(60, a=2, bx=0), capture(True, 0), capture(True, 1),
                   ins(59, a=1), ins(25, a=0, bx=0), ins(25, a=1, bx=1),
                   ins(9, a=2, b=2)], [number(30), number(40)], [two_getter], params=2, stack=3)
        _, make = self.build(body)
        self.assertEqual(make(10, 20)(), (30, 20))

    def test_capture_created_on_each_branch_retains_selected_value(self):
        body = fn([ins(1, a=1, c=1), jump(1, 5),
                   ins(60, a=2, bx=0), capture(True, 0), ins(9, a=2, b=2),
                   ins(25, a=0, bx=0), ins(60, a=2, bx=0), capture(True, 0),
                   ins(9, a=2, b=2)], [number(22)], [getter()], params=2, stack=3)
        _, make = self.build(body)
        self.assertEqual(make(10, False)(), 10)
        self.assertEqual(make(10, True)(), 22)

    def test_small_real_script_mock_api_order_and_module_environment(self):
        path = Path(os.environ.get('AMALUR_SMALL_LUA', ROOT / 'outputs' / 'reconstruction-v03' / 'small.lua'))
        source = path.read_text(encoding='utf-8')
        self.assertNotIn('UNRESOLVED function', source)
        lua = self.runtime()
        lua.execute('''
          events = {}
          behavior = {approach_actor = function(...)
            events[#events+1] = {'approach_actor', ...}
          end}
          GOR_ID = function(name)
            events[#events+1] = {'GOR_ID', name}
            return 'mock-actor-id'
          end
        ''')
        lua.execute(source)
        module = lua.globals().MQ14_Alyn_Laz_Defence
        self.assertIsNotNone(module)
        callback = module.on_creature_summoned
        self.assertEqual(lua.eval('getfenv')(callback)._NAME, 'MQ14_Alyn_Laz_Defence')
        callback('mock-summoned')
        events = lua.globals().events
        self.assertEqual(len(events), 2)
        self.assertEqual([events[1][i] for i in range(1, 3)], ['GOR_ID', 'NPC_MQ_DOK_AlynShir'])
        self.assertEqual([events[2][i] for i in range(1, 7)],
                         ['approach_actor', 'mock-summoned', 'mock-actor-id', 200, 926483, 364433])


if __name__ == '__main__':
    unittest.main(verbosity=2)
