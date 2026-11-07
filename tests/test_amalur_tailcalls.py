"""Canonical native tail call and owned-return obligations."""
import unittest
import test_amalur_loops_openlists as base
from amalur_reconstruct import ReconstructionError
from lupa.lua51 import LuaError
ins,fn,branch=base.ins,base.fn,base.branch
class TailCallRuntimeTests(unittest.TestCase):
 setUpClass=classmethod(base.LoopOpenListRuntimeTests.setUpClass.__func__)
 lift=base.LoopOpenListRuntimeTests.lift
 build=base.LoopOpenListRuntimeTests.build
 packed=base.LoopOpenListRuntimeTests.packed
 assert_unresolved=base.LoopOpenListRuntimeTests.assert_unresolved
 def test_tailcall_fixed_arguments_preserve_zero_and_nil_results(self):
  for op in (22,23):
   lua,run=self.build(fn([ins(op,b=3),ins(9,b=0)],params=3,stack=3))
   f=lua.eval('function(...) return select("#",...),...,nil end')
   self.assertEqual(self.packed(lua,run,f,7,None),[2,7,None])
   self.assertEqual(self.packed(lua,run,lua.eval('function() end'),7,None),[])
 def test_tailcall_open_arguments_preserve_trailing_nil(self):
  lua,run=self.build(fn([ins(61,a=1,b=0),ins(22,a=0,b=0),ins(9,a=0,b=0)],params=1,stack=2,varargs=True))
  f=lua.eval('function(...) return ... end')
  self.assertEqual(self.packed(lua,run,f,None,7,None),[None,7,None])
 def test_cached_tailcall_move_alias_survives_unrelated_write(self):
  lua,run=self.build(fn([ins(7,a=1,b=0),ins(26,a=2,b=2),ins(62,a=1,b=1),ins(9,a=1,b=0)],params=1,stack=3))
  self.assertEqual(self.packed(lua,run,lua.eval('function() return nil,8,nil end')),[None,8,None])
 def test_cached_tailcall_unknown_entry_cache_rejected(self):
  self.assert_unresolved(fn([ins(62,b=1),ins(9,b=0)],params=1,stack=1))
 def test_tailcall_nonfunction_domain_rejected(self):
  lua,run=self.build(fn([ins(22,b=1),ins(9,b=0)],params=1,stack=1))
  with self.assertRaisesRegex(LuaError,'tail-call'):run(1)
 def test_tailcall_noncanonical_result_encoding_rejected(self):
  self.assert_unresolved(fn([ins(22,b=1,c=2),ins(9,b=0)],params=1,stack=1))
 def test_tailcall_owned_return_must_match_base_and_open_count(self):
  for ret in (ins(9,a=1,b=0),ins(9,b=2),ins(5)):
   with self.subTest(ret=ret),self.assertRaises(ReconstructionError):self.lift(fn([ins(22,b=1),ret],params=1,stack=2))
 def test_external_jump_into_owned_return_rejected(self):
  with self.assertRaises(ReconstructionError):self.lift(fn([branch(28,0,2),ins(22,b=1),ins(9,b=0)],params=1,stack=1))
