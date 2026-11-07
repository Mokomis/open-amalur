"""Signed-int32 DIV obligations, distinct from Lua 5.1 floating division."""
import json
import os
from pathlib import Path
import unittest

import test_amalur_loops_openlists as base
import test_amalur_real_loops_openlists as real
from lupa.lua51 import LuaError

ins, fn = base.ins, base.fn


def number(value):
    return {'type': 'number', 'raw_hex': int(value).to_bytes(4, 'big', signed=True).hex()}


class IntegerDivisionRuntimeTests(unittest.TestCase):
    lift = base.LoopOpenListRuntimeTests.lift
    build = base.LoopOpenListRuntimeTests.build
    assert_unresolved = base.LoopOpenListRuntimeTests.assert_unresolved

    @classmethod
    def setUpClass(cls):
        path = Path(os.environ.get('AMALUR_NATIVE_PROFILE', base.ROOT / 'outputs' / 'native-script-profile.json'))
        cls.profile = json.loads(path.read_text(encoding='utf-8-sig'))

    def division(self):
        return fn([ins(40, a=2, b=0, c=1), ins(9, a=2, b=2)], params=2, stack=3)

    def test_signed_division_truncates_toward_zero_for_every_sign_pair(self):
        _, run = self.build(self.division())
        for left, right, expected in [(7, 3, 2), (-7, 3, -2), (7, -3, -2), (-7, -3, 2),
                                      (1, 2, 0), (-1, 2, 0), (0, -3, 0)]:
            with self.subTest(left=left, right=right):
                self.assertEqual(run(left, right), expected)

    def test_signed_division_boundary_values(self):
        _, run = self.build(self.division())
        for left, right, expected in [(-2147483648, 1, -2147483648), (2147483647, 1, 2147483647),
                                      (-2147483648, 2, -1073741824), (2147483647, 2, 1073741823),
                                      (2147483647, -2147483648, 0), (-2147483648, -2147483648, 1)]:
            with self.subTest(left=left, right=right):
                self.assertEqual(run(left, right), expected)

    def test_truncated_zero_has_native_integer_zero_representation(self):
        lua, run = self.build(self.division())
        observe = lua.eval('function(f, a, b) local result=f(a,b); return result == 0 and 1/result == math.huge end')
        for left, right in [(-1,2),(1,-2),(-0.0,2),(0,-2)]:
            with self.subTest(left=left,right=right):
                self.assertTrue(observe(run,left,right))

    def test_division_reads_both_operands_before_aliasing_destination(self):
        for destination in [0, 1]:
            with self.subTest(destination=destination):
                _, run = self.build(fn([ins(40, a=destination, b=0, c=1), ins(9, a=destination, b=2)],
                                       params=2, stack=2))
                self.assertEqual(run(-7, 3), -2)

    def test_division_register_and_constant_operand_matrix(self):
        cases = [
            (fn([ins(41, a=1, b=0, c=0), ins(9, a=1, b=2)], params=1, stack=2, constants=[number(17)]), (3,)),
            (fn([ins(40, a=1, b=0, c=256), ins(9, a=1, b=2)], params=1, stack=2, constants=[number(3)]), (17,)),
            (fn([ins(41, a=0, b=0, c=257), ins(9, a=0, b=2)], stack=1, constants=[number(17), number(3)]), ()),
        ]
        for body, args in cases:
            with self.subTest(word=body['instructions'][0]['word_hex']):
                _, run = self.build(body)
                self.assertEqual(run(*args), 5)

    def test_division_constant_selector_uses_all_eight_index_bits(self):
        constants = [number(0) for _ in range(256)]
        constants[255] = number(17)
        _, left = self.build(fn([ins(41, a=1, b=255, c=0), ins(9, a=1, b=2)], params=1, stack=2, constants=constants))
        self.assertEqual(left(3), 5)
        constants[255] = number(3)
        _, right = self.build(fn([ins(40, a=1, b=0, c=511), ins(9, a=1, b=2)], params=1, stack=2, constants=constants))
        self.assertEqual(right(17), 5)

    def test_division_zero_and_signed_overflow_are_explicitly_rejected(self):
        _, run = self.build(self.division())
        for left, right in [(1, 0), (0, 0), (-2147483648, -1)]:
            with self.subTest(left=left, right=right):
                with self.assertRaisesRegex(LuaError, 'Amalur|division'):
                    run(left, right)

    def test_division_rejects_noninteger_and_custom_metamethod_domains(self):
        lua, run = self.build(self.division())
        for value in [0.5, '7', None, True, 2147483648, -2147483649, float('nan'), float('inf'),
                      lua.eval("setmetatable({}, {__div=function() error('metamethod must not run') end})")]:
            with self.subTest(value=str(value)):
                with self.assertRaisesRegex(LuaError, 'Amalur|division'):
                    run(value, 2)
                with self.assertRaisesRegex(LuaError, 'Amalur|division'):
                    run(2, value)

    def test_division_does_not_claim_hidden_cached_result(self):
        field = {'type': 'string', 'value': {'bytes_hex': 'field'.encode().hex()}}
        self.assert_unresolved(fn([ins(40, a=1, b=0, c=256), ins(67, a=2, b=1, c=1),
                                   ins(70), ins(70), ins(9, a=2, b=2)],
                                  params=1, stack=3, constants=[number(2), field]))


class RealIntegerDivisionRuntimeTests(unittest.TestCase):
    build = real.RealLoopOpenListRuntimeTests.build

    def test_real_sq02_integer_division_truncates_halves(self):
        _, run = self.build('441939.lua_bxml',
                            '88e5baf1fb05dae012799fe3ec5afb9e831a9444d22d0092b3db9880dc84bf8c',
                            '0/0', ['50010001', '12040001', '12020000'], corpus=False)
        for value, expected in [(-2147483648, -1073741824), (2147483647, 1073741823),
                                (-3, -1), (-1, 0), (0, 0), (1, 0), (3, 1)]:
            with self.subTest(value=value):
                self.assertEqual(run(value), expected)


if __name__ == '__main__':
    unittest.main(verbosity=2)
