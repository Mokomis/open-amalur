"""Native-derived loop/list obligations executed in isolated Lua 5.1 on Windows.

These exercise generated code with synthetic inputs, not the game's Havok VM.
Expected numeric-loop sequences deliberately differ from stock Lua for short
reversed ranges: the native preparation divides with truncation toward zero.
"""
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'python-libs'))
sys.path.insert(0, str(ROOT / 'src'))
from lupa.lua51 import LUA_VERSION, LuaError, LuaRuntime
from amalur_script import decode_instruction
from amalur_reconstruct import reconstruct


def ins(op, a=0, b=0, c=0, bx=None):
    word = (op << 25) | a | (((b << 9) | c) << 8 if bx is None else bx << 8)
    return decode_instruction(word, 0, 0)


def branch(op, pc, target, a=0):
    return ins(op, a=a, bx=65535 + target - pc - 1)


def fn(code, params=0, stack=8, varargs=False, constants=()):
    return {'instructions': [dict(row, pc=i, file_offset=0x100 + i * 4) for i, row in enumerate(code)],
            'constants': list(constants), 'children': [], 'parameter_count': params,
            'maximum_stack_size': stack, 'upvalue_count': 0, 'vararg_flags': 2 if varargs else 0}


class LoopOpenListRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert tuple(LUA_VERSION) == (5, 1)
        path = Path(os.environ.get('AMALUR_NATIVE_PROFILE', ROOT / 'outputs' / 'native-script-profile.json'))
        cls.profile = json.loads(path.read_text(encoding='utf-8-sig'))

    def lift(self, body):
        return reconstruct({'input_sha256': '0' * 64, 'chunk': {'root_function': body}}, self.profile)

    def build(self, body):
        ir, source = self.lift(body)
        self.assertTrue(ir['root_function']['body_emittable'],
                        json.dumps(ir['root_function']['unknowns'], indent=2))
        lua = LuaRuntime(unpack_returned_tuples=True, register_eval=False, register_builtins=False)
        lua.execute("debug.sethook(function() error('loop/list fixture instruction budget exceeded') end, '', 100000)")
        lua.execute('io=nil; os=nil; python=nil; dofile=nil; loadfile=nil; require=nil; debug=nil')
        runner = lua.eval('function(...)\n' + source + '\nend')
        return lua, runner

    def packed(self, lua, runner, *args):
        pack = lua.eval("function(f, ...) local function pack(...) return {n=select('#', ...), ...} end return pack(f(...)) end")
        result = pack(runner, *args)
        return [result[i] for i in range(1, result.n + 1)]

    def assert_unresolved(self, body):
        ir, source = self.lift(body)
        self.assertFalse(ir['root_function']['body_emittable'])
        self.assertIn('UNRESOLVED', source)

    def test_open_results_preserve_nil_count_beyond_nominal_register_window(self):
        lua, run = self.build(fn([ins(2, b=1, c=0), ins(9, b=0)], params=1, stack=2))
        producer = lua.eval('function() return nil, 7, nil, 9, nil end')
        self.assertEqual(self.packed(lua, run, producer), [None, 7, None, 9, None])

    def test_open_results_zero_values_are_not_one_nil(self):
        lua, run = self.build(fn([ins(2, b=1, c=0), ins(9, b=0)], params=1, stack=1))
        self.assertEqual(self.packed(lua, run, lua.eval('function() end')), [])
        self.assertEqual(self.packed(lua, run, lua.eval('function() return nil end')), [None])

    def test_open_call_does_not_preserve_known_registers_in_reused_callee_window(self):
        # Native callees reuse the caller tail even when the result mover itself
        # does not nil-fill. Fixed reads cannot rely on pre-call tail contents.
        self.assert_unresolved(fn([ins(2, b=1, c=0), ins(9, a=1, b=3)], params=3, stack=3))

    def test_open_vararg_copy_preserves_existing_cells_beyond_actual_top(self):
        lua, run = self.build(fn([ins(61, b=0), ins(9, a=0, b=3)], params=2, stack=2, varargs=True))
        self.assertEqual(self.packed(lua, run, 'old-one', 'old-two'), ['old-one', 'old-two'])
        self.assertEqual(self.packed(lua, run, 'old-one', 'old-two', 7), [7, 'old-two'])
        self.assertEqual(self.packed(lua, run, 'old-one', 'old-two', 7, None), [7, None])

    def test_fixed_call_nil_clears_tail_to_frame_bound(self):
        lua, run = self.build(fn([ins(2, b=1, c=2), ins(9, a=0, b=4)], params=3, stack=3))
        self.assertEqual(self.packed(lua, run, lua.eval('function() return 7 end'), 'old-one', 'old-two'),
                         [7, None, None])

    def test_open_results_with_fixed_input_argument_list(self):
        lua, run = self.build(fn([ins(2, b=3, c=0), ins(9, b=0)], params=3, stack=3))
        producer = lua.eval("function(...) return select('#', ...), ... end")
        self.assertEqual(self.packed(lua, run, producer, 4, None), [2, 4, None])

    def test_open_varargs_roundtrip_retains_trailing_nil(self):
        lua, run = self.build(fn([ins(61, a=0, b=0), ins(9, a=0, b=0)], stack=1, varargs=True))
        self.assertEqual(self.packed(lua, run, None, 8, None), [None, 8, None])
        self.assertEqual(self.packed(lua, run), [])

    def test_open_varargs_exclude_fixed_parameters(self):
        lua, run = self.build(fn([ins(61, a=1, b=0), ins(9, a=1, b=0)], params=1, stack=2, varargs=True))
        self.assertEqual(self.packed(lua, run, 'fixed', 'extra', None), ['extra', None])

    def test_fixed_vararg_load_clears_native_extra_slot(self):
        lua, run = self.build(fn([ins(61, a=0, b=3), ins(9, a=0, b=4)], stack=3, varargs=True))
        self.assertEqual(self.packed(lua, run, 7, 8, 9), [7, 8, None])
        self.assertEqual(self.packed(lua, run, 7), [7, None, None])
        self.assertEqual(self.packed(lua, run), [None, None, None])

    def test_fixed_zero_value_vararg_load_still_nil_fills_destination(self):
        lua, run = self.build(fn([ins(61, a=0, b=1), ins(9, a=0, b=2)], stack=1, varargs=True))
        self.assertEqual(self.packed(lua, run, 'ignored'), [None])

    def test_open_return_keeps_fixed_prefix_before_varargs(self):
        lua, run = self.build(fn([ins(61, a=1, b=0), ins(9, a=0, b=0)], params=1, stack=2, varargs=True))
        self.assertEqual(self.packed(lua, run, 'prefix', None, 3, None), ['prefix', None, 3, None])
        self.assertEqual(self.packed(lua, run, 'prefix'), ['prefix'])

    def test_vararg_producer_feeds_open_argument_and_result_call(self):
        lua, run = self.build(fn([ins(61, a=1, b=0), ins(2, a=0, b=0, c=0), ins(9, b=0)],
                                 params=1, stack=2, varargs=True))
        callee = lua.eval("function(...) return select('#', ...), ... end")
        self.assertEqual(self.packed(lua, run, callee, 1, None, 3, None), [4, 1, None, 3, None])
        self.assertEqual(self.packed(lua, run, callee), [0])

    def test_chained_open_calls_pass_exact_producer_count(self):
        lua, run = self.build(fn([ins(2, a=1, b=1, c=0), ins(2, a=0, b=0, c=0), ins(9, b=0)],
                                 params=2, stack=2))
        consumer = lua.eval("function(...) return select('#', ...), ... end")
        producer = lua.eval('function() return 5, nil, 6, nil end')
        self.assertEqual(self.packed(lua, run, consumer, producer), [4, 5, None, 6, None])
        self.assertEqual(self.packed(lua, run, consumer, lua.eval('function() end')), [0])

    def test_open_call_includes_prefix_arguments(self):
        lua, run = self.build(fn([ins(2, a=2, b=1, c=0), ins(2, a=0, b=0, c=0), ins(9, b=0)],
                                 params=3, stack=3))
        consumer = lua.eval("function(...) return select('#', ...), ... end")
        self.assertEqual(self.packed(lua, run, consumer, 'prefix', lua.eval('function() return nil, 4 end')),
                         [3, 'prefix', None, 4])

    def test_open_arguments_with_fixed_result_count_truncate_and_pad(self):
        lua, run = self.build(fn([ins(61, a=1, b=0), ins(2, a=0, b=0, c=3), ins(9, b=3)],
                                 params=1, stack=3, varargs=True))
        self.assertEqual(self.packed(lua, run, lua.eval('function(...) return ... end'), 7, None, 9), [7, None])
        self.assertEqual(self.packed(lua, run, lua.eval('function() return 8 end')), [8, None])

    def test_open_return_without_known_top_producer_is_unresolved(self):
        self.assert_unresolved(fn([ins(9, b=0)], params=1, stack=2))

    def test_open_call_without_known_top_producer_is_unresolved(self):
        self.assert_unresolved(fn([ins(2, b=0, c=2), ins(9, b=2)], params=1, stack=2))

    def test_branch_cannot_bypass_open_result_producer(self):
        self.assert_unresolved(fn([ins(1, a=1, c=1), branch(28, 1, 3),
                                   ins(2, a=0, b=1, c=0), ins(9, a=0, b=0)], params=2, stack=2))

    def test_open_result_join_with_different_bases_is_unresolved(self):
        self.assert_unresolved(fn([ins(1, a=2, c=1), branch(28, 1, 4),
                                   ins(2, a=0, b=1, c=0), branch(28, 3, 5),
                                   ins(2, a=1, b=1, c=0), ins(9, a=0, b=0)], params=3, stack=3))

    def test_open_result_join_with_consistent_base_preserves_selected_producer(self):
        lua, run = self.build(fn([ins(1, a=1, c=1), branch(28, 1, 4),
                                 ins(2, a=0, b=1, c=0), branch(28, 3, 6),
                                 ins(7, a=0, b=2), ins(2, a=0, b=1, c=0),
                                 ins(9, a=0, b=0)], params=3, stack=3))
        first = lua.eval('function() return 1, nil end')
        second = lua.eval('function() return nil, 2, nil end')
        self.assertEqual(self.packed(lua, run, first, False, second), [1, None])
        self.assertEqual(self.packed(lua, run, first, True, second), [None, 2, None])

    def test_fixed_call_results_do_not_claim_dynamic_top_provenance(self):
        self.assert_unresolved(fn([ins(2, a=0, b=1, c=2), ins(9, a=0, b=0)], params=1, stack=2))

    def test_vararg_opcode_in_nonvararg_function_is_unresolved(self):
        self.assert_unresolved(fn([ins(61, b=0), ins(9, b=0)], stack=2))

    def test_open_call_cannot_leave_escaped_capture_in_reused_callee_window(self):
        child = fn([ins(32, a=0, b=0), ins(9, a=0, b=2)], stack=1)
        child['upvalue_count'] = 1
        body = fn([ins(60, a=0, bx=0), ins(70, a=1, bx=3),
                   ins(2, a=2, b=1, c=0), ins(9, a=0, b=2)], params=4, stack=4)
        body['children'] = [child]
        self.assert_unresolved(body)

    def test_closed_capture_is_detached_before_callee_reuses_window(self):
        child = fn([ins(32, a=0, b=0), ins(9, a=0, b=2)], stack=1)
        child['upvalue_count'] = 1
        body = fn([ins(60, a=0, bx=0), ins(70, a=1, bx=3), ins(59, a=3),
                   ins(2, a=2, b=1, c=0), ins(9, a=0, b=2)], params=4, stack=4)
        body['children'] = [child]
        lua, run = self.build(body)
        getter = run(None, None, lua.eval("function() return 'new-value', nil end"), 'captured-before-close')
        self.assertEqual(getter(), 'captured-before-close')

    def test_fixed_call_also_rejects_live_capture_in_callee_window(self):
        child = fn([ins(32, a=0, b=0), ins(9, a=0, b=2)], stack=1)
        child['upvalue_count'] = 1
        body = fn([ins(60, a=0, bx=0), ins(70, a=1, bx=3),
                   ins(2, a=2, b=1, c=2), ins(9, a=0, b=2)], params=4, stack=4)
        body['children'] = [child]
        self.assert_unresolved(body)

    def numeric(self):
        # R0=observer, R1..R3=start/limit/step, R4=visible index.
        # Body calls a copy of observer so loop-control registers stay private.
        return fn([branch(56, 0, 4, a=1), ins(7, a=5, b=0), ins(7, a=6, b=4),
                   ins(2, a=5, b=2, c=1), branch(57, 4, 1, a=1), ins(9, b=1)], params=4, stack=7)

    def sequence(self, start, limit, step):
        lua, run = self.build(self.numeric())
        lua.execute('events = {}; observer = function(value) events[#events+1] = value end')
        run(lua.globals().observer, start, limit, step)
        return [lua.globals().events[i] for i in range(1, len(lua.globals().events) + 1)]

    def test_numeric_loop_positive_and_negative_steps(self):
        self.assertEqual(self.sequence(1, 5, 2), [1, 3, 5])
        self.assertEqual(self.sequence(5, 1, -2), [5, 3, 1])

    def test_numeric_loop_zero_iterations(self):
        self.assertEqual(self.sequence(5, 1, 1), [])
        self.assertEqual(self.sequence(1, 5, -1), [])

    def test_numeric_loop_short_reversed_range_matches_native_quotient(self):
        self.assertEqual(self.sequence(2, 1, 2), [2])
        self.assertEqual(self.sequence(1, 2, -2), [1])

    def test_numeric_loop_wraps_signed32_difference_and_counter(self):
        self.assertEqual(self.sequence(2147483647, -2147483648, 1), [2147483647, -2147483648])
        self.assertEqual(self.sequence(-2147483648, 2147483647, -1), [-2147483648, 2147483647])

    def test_numeric_loop_count_above_native_cap_means_no_iterations(self):
        self.assertEqual(self.sequence(0, 1073741824, 1), [])

    def test_numeric_loop_division_hazards_and_unmodeled_domains_rejected(self):
        lua, run = self.build(self.numeric())
        observer = lua.eval('function(value) end')
        for start, limit, step in [(0, 1, 0), (0, -2147483648, -1),
                                   (0.5, 2, 1), ('1', 2, 1), (0, 2, None)]:
            with self.subTest(start=start, limit=limit, step=step):
                with self.assertRaisesRegex(LuaError, 'Amalur|numeric'):
                    run(observer, start, limit, step)

    def test_numeric_loop_without_prepare_proof_is_unresolved(self):
        self.assert_unresolved(fn([branch(57, 0, 0), ins(9, b=1)], params=4, stack=4))

    def test_numeric_loop_private_count_cannot_be_overwritten(self):
        body = self.numeric()
        body['instructions'][1] = dict(ins(7, a=2, b=0), pc=1, file_offset=0x104)
        self.assert_unresolved(body)

    def test_numeric_loop_private_count_cannot_escape_after_loop(self):
        body = self.numeric()
        body['instructions'][5] = dict(ins(9, a=2, b=2), pc=5, file_offset=0x114)
        self.assert_unresolved(body)

    def test_capture_created_before_loop_cannot_observe_internal_count(self):
        child = fn([ins(32, a=0, b=0), ins(9, a=0, b=2)], stack=1)
        child['upvalue_count'] = 1
        body = fn([ins(60, a=4, bx=0), ins(70, a=1, bx=1),
                   branch(56, 2, 4, a=0), ins(7, a=5, b=4),
                   branch(57, 4, 3, a=0), ins(9, a=4, b=2)], params=3, stack=6)
        body['children'] = [child]
        self.assert_unresolved(body)

    def test_numeric_loop_private_count_can_be_replaced_after_loop(self):
        body = self.numeric()
        # Use the native-confirmed LOADNIL mapping from the selected profile.
        loadnil = next(int(op) for op, spec in self.profile['opcodes'].items() if spec['kind'] == 'loadnil')
        code = body['instructions'][:5] + [ins(loadnil, a=2, b=2), ins(9, a=2, b=2)]
        lua, run = self.build(fn(code, params=4, stack=7))
        self.assertEqual(self.packed(lua, run, lua.eval('function(value) end'), 5, 1, 1), [None])

    def test_numeric_visible_index_is_initialized_even_with_zero_iterations(self):
        body = self.numeric()
        body['instructions'][5] = dict(ins(9, a=4, b=2), pc=5, file_offset=0x114)
        lua, run = self.build(body)
        self.assertEqual(self.packed(lua, run, lua.eval('function(value) end'), 5, 1, 1), [5])

    def generic(self, results=1):
        # R0 observer, R1 iterator, R2 state, R3 control at entry.
        # Keep observer below A: native fixed-result calls clear the tail.
        code = [branch(28, 0, 4 + (results - 1)),
                ins(7, a=6, b=0), ins(7, a=7, b=4)]
        if results == 2:
            code.append(ins(7, a=8, b=5))
        code.append(ins(2, a=6, b=results + 1, c=1))
        pc = len(code)
        code.extend([ins(14, a=1, c=results), branch(28, pc + 1, 1), ins(9, a=3, b=2)])
        return fn(code, params=4, stack=9)

    def test_generic_loop_false_first_result_continues_and_nil_stops(self):
        lua, run = self.build(self.generic())
        lua.execute('''
          events = {}; controls = {}; count = 0
          iterator = function(state, control)
            assert(state == 'state')
            controls[#controls+1] = {value=control}
            count = count + 1
            if count == 1 then return false end
            if count == 2 then return 'last' end
            return nil
          end
          observer = function(value) events[#events+1] = {value=value} end
        ''')
        self.assertEqual(self.packed(lua, run, lua.globals().observer, lua.globals().iterator, 'state', 'initial'), [None])
        events, controls = lua.globals().events, lua.globals().controls
        self.assertEqual([events[i].value for i in range(1, len(events) + 1)], [False, 'last'])
        self.assertEqual([controls[i].value for i in range(1, len(controls) + 1)], ['initial', False, 'last'])

    def test_generic_loop_fixed_results_pad_nil_and_truncate_excess(self):
        lua, run = self.build(self.generic(2))
        lua.execute('''
          events = {}; count = 0
          iterator = function(state, control)
            count = count + 1
            if count == 1 then return 1 end
            if count == 2 then return 2, 'value', 'ignored' end
            return nil, 'termination value'
          end
          observer = function(...) events[#events+1] = {n=select('#', ...), ...} end
        ''')
        self.assertEqual(self.packed(lua, run, lua.globals().observer, lua.globals().iterator, None, None), [None])
        events = lua.globals().events
        self.assertEqual(len(events), 2)
        self.assertEqual([[events[i].n, events[i][1], events[i][2]] for i in range(1, 3)],
                         [[2, 1, None], [2, 2, 'value']])

    def test_generic_loop_with_pending_open_top_is_unresolved(self):
        self.assert_unresolved(fn([ins(61, a=3, b=0), ins(14, a=0, c=1),
                                   branch(28, 2, 1), ins(9, b=1)], params=3, stack=4, varargs=True))

    def test_generic_iterator_temporary_call_does_not_clear_caller_tail(self):
        lua, run = self.build(fn([ins(14, a=0, c=1), branch(28, 1, 0), ins(9, a=4, b=2)],
                                params=5, stack=5))
        iterator = lua.eval('function(state, control) if control == nil then return false end return nil end')
        self.assertEqual(run(iterator, None, None, 'old-result', 'tail-sentinel'), 'tail-sentinel')


if __name__ == '__main__':
    unittest.main(verbosity=2)
