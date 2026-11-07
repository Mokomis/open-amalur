"""Windows Lua5.1 obligations for native-confirmed legacy arg-table emission.

Global-state +0x154 is n: state_init -> cached_string_init index1 -> static
record0x19741e4 -> CRT initializer0x135e880 writes literal n at0x19741f0.
"""
import json
import os
from pathlib import Path
import unittest

import test_amalur_loops_openlists as base

ins = base.ins


def legacy(code, params=0, stack=8):
    body = base.fn(code, params=params, stack=stack, varargs=True)
    body["vararg_flags"] = 7
    return body


class LegacyVarargRuntimeTests(unittest.TestCase):
    lift = base.LoopOpenListRuntimeTests.lift
    build = base.LoopOpenListRuntimeTests.build
    packed = base.LoopOpenListRuntimeTests.packed
    assert_unresolved = base.LoopOpenListRuntimeTests.assert_unresolved

    @classmethod
    def setUpClass(cls):
        path = Path(os.environ.get("AMALUR_NATIVE_PROFILE", base.ROOT / "outputs/native-script-profile.json"))
        cls.profile = json.loads(path.read_text(encoding="utf-8-sig"))

    def test_zero_extra_args_still_create_table_and_count(self):
        lua, run = self.build(legacy([ins(9, a=0, b=2)], stack=1))
        observe = lua.eval("function(f) local a=f(); return type(a)=='table' and a.n==0 and next(a)=='n' end")
        self.assertTrue(observe(run))

    def test_count_includes_trailing_nil_and_false(self):
        lua, run = self.build(legacy([ins(9, a=0, b=2)], stack=1))
        observe = lua.eval("function(f) local a=f(nil,false,7,nil); return a.n==4 and a[1]==nil and a[2]==false and a[3]==7 and a[4]==nil and a[0]==nil end")
        self.assertTrue(observe(run))

    def test_fixed_parameters_are_excluded_from_arg_table(self):
        lua, run = self.build(legacy([ins(9, a=2, b=2)], params=2, stack=3))
        observe = lua.eval("function(f) local a=f('fixed-one','fixed-two','extra',nil); return a.n==2 and a[1]=='extra' and a[2]==nil end")
        self.assertTrue(observe(run))

    def test_missing_fixed_parameters_remain_nil_and_extra_count_zero(self):
        lua, run = self.build(legacy([ins(9, a=0, b=4)], params=2, stack=3))
        observe = lua.eval("function(f) local a,b,args=f('fixed'); return a=='fixed' and b==nil and args.n==0 end")
        self.assertTrue(observe(run))

    def test_legacy_arg_mutation_does_not_mutate_vararg_backing_list(self):
        # Native arg is a copy. A callback mutates both array and count before
        # the body requests original varargs; fixed CALL clears register tail.
        lua, run = self.build(legacy([ins(2, a=0, b=2, c=1), ins(61, a=0, b=0), ins(9, a=0, b=0)],
                                     params=1, stack=3))
        callback = lua.eval("function(arg) arg[1]='changed'; arg[3]=nil; arg.n=0 end")
        self.assertEqual(self.packed(lua, run, callback, "original", None, False, None),
                         ["original", None, False, None])

    def test_array_copy_preserves_reference_identity(self):
        lua, run = self.build(legacy([ins(9, a=0, b=2)], stack=1))
        observe = lua.eval("function(f) local t={}; local a=f(t); return a[1]==t and a.n==1 end")
        self.assertTrue(observe(run))

    def test_every_invocation_gets_a_distinct_table(self):
        lua, run = self.build(legacy([ins(9, a=0, b=2)], stack=1))
        observe = lua.eval("function(f) local a,b=f(1),f(1); a[1]=2; return a~=b and b[1]==1 end")
        self.assertTrue(observe(run))

    def test_legacy_table_can_be_captured_before_explicit_definition(self):
        child = base.fn([ins(32, a=0, b=0), ins(9, a=0, b=2)], stack=1)
        child["upvalue_count"] = 1
        body = legacy([ins(60, a=1, bx=0), ins(70, a=1, bx=0), ins(9, a=1, b=2)], stack=2)
        body["children"] = [child]
        lua, run = self.build(body)
        observe = lua.eval("function(f) local closure=f(4,nil); local a=closure(); return a.n==2 and a[1]==4 and a[2]==nil end")
        self.assertTrue(observe(run))

    def test_legacy_initialization_does_not_admit_uninitialized_neighbor(self):
        self.assert_unresolved(legacy([ins(9, a=1, b=2)], stack=2))

    def test_legacy_table_slot_must_fit_declared_frame(self):
        # All explicit operands fit; only the implicit R[parameter_count] slot
        # lies outside the declared frame. Do not silently allocate a new cell.
        self.assert_unresolved(legacy([ins(9, a=0, b=2)], params=1, stack=1))


if __name__ == "__main__":
    unittest.main()
