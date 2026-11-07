"""Targeted native-cache dataflow regressions; run on Windows with unittest."""
import unittest

from cache_flow import analyze_cache_aliases, TARGET_SHA256


def row(pc, op, a=0, b=0, successors=(), writes=(), **extra):
    value = dict(pc=pc, opcode=op, kind="fixture", A=a, B=b, C=0,
                 successors=list(successors), writes=list(writes), edge_writes={})
    value.update(extra)
    return value


def solve(rows, frame=8, unconfirmed=()):
    profile = dict(binary_sha256=TARGET_SHA256, opcodes={
        str(r["opcode"]): dict(confirmation="native_static", evidence=["fixture"])
        for r in rows if r["opcode"] not in unconfirmed
    })
    return analyze_cache_aliases(rows, profile, frame)


class NativeCacheFlowTests(unittest.TestCase):
    def test_nonadjacent_producer_survives_unrelated_write(self):
        result = solve([row(0, 6, successors=[2], writes=[0]),
                        row(2, 25, a=1, successors=[3], writes=[1]),
                        row(3, 63)])
        self.assertTrue(result[3]["cache_register_proven"])

    def test_getfield_and_self_are_producers(self):
        for op in (0, 8):
            with self.subTest(op=op):
                result = solve([row(0, op, a=2, successors=[3], writes=[2, 3]),
                                row(3, 65, a=2)])
                self.assertTrue(result[3]["cache_register_proven"])
                self.assertEqual(result[3]["cached_aliases_in"], [2])

    def test_different_branch_producers_can_prove_same_register(self):
        result = solve([row(0, 4, successors=[1, 3]),
                        row(1, 6, a=2, successors=[2], writes=[2]),
                        row(2, 28, successors=[4]),
                        row(3, 32, a=2, successors=[4], writes=[2]),
                        row(4, 65, a=2)])
        self.assertTrue(result[4]["cache_register_proven"])
        self.assertEqual(result[4]["cache_predecessor_pcs"], [2, 3])

    def test_one_branch_without_producer_rejects(self):
        result = solve([row(0, 4, successors=[1, 3]),
                        row(1, 6, a=2, successors=[4], writes=[2]),
                        row(3, 25, a=2, successors=[4], writes=[2]),
                        row(4, 65, a=2)])
        self.assertFalse(result[4]["cache_register_proven"])

    def test_loop_backedge_overwrite_removes_proof(self):
        for written, proven in ((1, True), (0, False)):
            with self.subTest(written=written):
                result = solve([row(0, 6, successors=[1], writes=[0]),
                                row(1, 65, successors=[2, 3]),
                                row(2, 25, a=written, successors=[1], writes=[written]),
                                row(3, 9)])
                self.assertEqual(result[1]["cache_register_proven"], proven)

    def test_loop_cannot_invent_entry_cache_value(self):
        result = solve([row(0, 25, successors=[1], writes=[0]),
                        row(1, 65, successors=[2, 3]),
                        row(2, 6, successors=[1], writes=[0]), row(3, 9)])
        self.assertFalse(result[1]["cache_register_proven"])

    def test_not_caches_input_and_move_preserves_alias(self):
        result = solve([row(0, 48, a=1, b=0, successors=[1], writes=[1]),
                        row(1, 7, a=2, b=0, successors=[2], writes=[2]),
                        row(2, 48, a=0, b=0, successors=[3], writes=[0]),
                        row(3, 66, a=2, b=2, successors=[4], writes=[2]),
                        row(4, 65, a=2)])
        self.assertEqual(result[1]["cached_aliases_in"], [0])
        self.assertEqual(result[2]["cached_aliases_in"], [0, 2])
        self.assertEqual(result[3]["cached_aliases_in"], [2])
        self.assertTrue(result[3]["cache_register_proven"])
        self.assertFalse(result[4]["cache_register_proven"])

    def test_calls_invalidate_even_when_result_register_matches(self):
        for op in (2, 3, 14, 22, 23, 24, 29, 30, 31, 62, 63):
            with self.subTest(op=op):
                result = solve([row(0, 6, successors=[1], writes=[0]),
                                row(1, op, successors=[2], writes=[0]),
                                row(2, 65)])
                self.assertFalse(result[2]["cache_register_proven"])

    def test_cached_tailcall_requires_input_relation(self):
        for producer, proven in ((6, True), (25, False)):
            result = solve([row(0, producer, successors=[1], writes=[0]), row(1, 62)])
            self.assertEqual(result[1]["cache_register_proven"], proven)

    def test_possible_or_definite_write_kills_alias(self):
        for effect in ("writes", "may_writes", "kills"):
            with self.subTest(effect=effect):
                change = row(1, 58, successors=[2])
                change[effect] = [3]
                result = solve([row(0, 6, a=3, successors=[1], writes=[3]), change,
                                row(2, 65, a=3)])
                self.assertFalse(result[2]["cache_register_proven"])

    def test_forloop_conditional_writes_only_kill_taken_edge(self):
        result = solve([row(0, 6, a=3, successors=[1], writes=[3]),
                        row(1, 57, successors=[2, 3], edge_writes={"2": [0, 1, 3]}),
                        row(2, 65, a=3), row(3, 65, a=3)])
        self.assertFalse(result[2]["cache_register_proven"])
        self.assertTrue(result[3]["cache_register_proven"])

    def test_testset_adds_alias_only_on_taken_edge(self):
        result = solve([row(0, 6, a=1, successors=[1], writes=[1]),
                        row(1, 55, a=2, b=1, successors=[2, 3], jump_target=2,
                            fallthrough_target=3, edge_writes={"2": [2]}),
                        row(2, 65, a=2), row(3, 65, a=2)])
        self.assertTrue(result[2]["cache_register_proven"])
        self.assertFalse(result[3]["cache_register_proven"])

    def test_merged_testset_conditional_overwrite_is_not_definite(self):
        for cached, source, proven in ((1, 1, False), (2, 1, False), (2, 2, True)):
            with self.subTest(cached=cached, source=source):
                result = solve([row(0, 6, a=cached, successors=[1], writes=[cached]),
                                row(1, 55, a=2, b=source, successors=[2],
                                    jump_target=2, fallthrough_target=2),
                                row(2, 65, a=2)])
                self.assertEqual(result[2]["cache_register_proven"], proven)

    def test_unconfirmed_or_unknown_handler_invalidates(self):
        for op, missing in ((25, (25,)), (78, ())):
            result = solve([row(0, 6, successors=[1], writes=[0]),
                            row(1, op, successors=[2]), row(2, 65)], unconfirmed=missing)
            self.assertFalse(result[2]["cache_register_proven"])

    def test_unreachable_predecessor_does_not_poison_proof(self):
        result = solve([row(0, 6, successors=[2], writes=[0]),
                        row(1, 25, successors=[2], writes=[0]), row(2, 65)])
        self.assertTrue(result[2]["cache_register_proven"])
        self.assertNotIn(1, result)

    def test_global_setter_callback_is_conservatively_invalidating(self):
        result = solve([row(0, 6, successors=[1], writes=[0]),
                        row(1, 27, successors=[2]), row(2, 65)])
        self.assertFalse(result[2]["cache_register_proven"])


if __name__ == "__main__":
    unittest.main()
