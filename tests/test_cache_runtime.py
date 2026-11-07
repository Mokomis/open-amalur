"""Windows Lua5.1 checks of CFG cache-proof integration and NOT_R1 emission."""
import json
import os
from pathlib import Path
import unittest

import test_amalur_loops_openlists as base

ins, fn = base.ins, base.fn


class CacheRuntimeTests(unittest.TestCase):
    lift = base.LoopOpenListRuntimeTests.lift
    build = base.LoopOpenListRuntimeTests.build
    packed = base.LoopOpenListRuntimeTests.packed
    assert_unresolved = base.LoopOpenListRuntimeTests.assert_unresolved

    @classmethod
    def setUpClass(cls):
        path = Path(os.environ.get("AMALUR_NATIVE_PROFILE", base.ROOT / "outputs/native-script-profile.json"))
        cls.profile = json.loads(path.read_text(encoding="utf-8-sig"))

    def test_nonadjacent_cached_callable_survives_unrelated_constant(self):
        body = fn([ins(7, a=1, b=0), ins(25, a=2, bx=0), ins(63, a=1, b=1, c=2), ins(9, a=1, b=2)],
                  params=1, stack=3, constants=[{"type": "boolean", "value": True}])
        lua, run = self.build(body)
        self.assertEqual(run(lua.eval("function() return 37 end")), 37)

    def test_ordinary_getfield_proves_cached_not_input(self):
        body = fn([ins(0, a=1, b=0, c=0), ins(70), ins(70), ins(66, a=1, b=1), ins(9, a=1, b=2)],
                  params=1, stack=2, constants=[{"type": "string", "value": {"bytes_hex": "76616c7565"}}])
        lua, run = self.build(body)
        for value, expected in ((None, True), (False, True), (True, False), (0, False), ("", False)):
            with self.subTest(value=value):
                table = lua.table()
                table["value"] = value
                self.assertEqual(run(table), expected)

    def test_not_result_is_not_its_cache_input(self):
        self.assert_unresolved(fn([ins(48, a=0, b=0), ins(66, a=1, b=0), ins(9, a=1, b=2)],
                                  params=1, stack=2))

    def test_not_source_register_survives_distinct_destination(self):
        lua, run = self.build(fn([ins(48, a=1, b=0), ins(66, a=2, b=0), ins(9, a=1, b=3)],
                                params=1, stack=3))
        for value, expected in ((None, True), (False, True), (True, False), (0, False)):
            with self.subTest(value=value):
                self.assertEqual(self.packed(lua, run, value), [expected, expected])

    def test_call_result_does_not_establish_new_cached_callable(self):
        self.assert_unresolved(fn([ins(7, a=1, b=0), ins(2, a=1, b=1, c=2),
                                   ins(63, a=1, b=1, c=2), ins(9, a=1, b=2)], params=1, stack=2))

    def test_overwritten_alias_cannot_feed_cached_not(self):
        self.assert_unresolved(fn([ins(7, a=1, b=0), ins(13, a=1, b=0),
                                   ins(66, a=2, b=1), ins(9, a=2, b=2)], params=1, stack=3))

    def test_function_entry_does_not_assume_cache_equals_parameter(self):
        self.assert_unresolved(fn([ins(66, a=1, b=0), ins(9, a=1, b=2)], params=1, stack=2))


if __name__ == "__main__":
    unittest.main()
