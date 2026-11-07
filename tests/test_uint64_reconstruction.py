import unittest
from pathlib import Path
import test_amalur_loops_openlists as base
from lupa.lua51 import LuaError
from amalur_reconstruct import ReconstructionError
ins,fn=base.ins,base.fn
class Uint64ReconstructionTests(unittest.TestCase):
 setUpClass=classmethod(base.LoopOpenListRuntimeTests.setUpClass.__func__)
 lift=base.LoopOpenListRuntimeTests.lift
 build=base.LoopOpenListRuntimeTests.build
 def constant(self,raw):return {'type':'uint64','raw_hex':raw,'value':int(raw,16)}
 def setup(self,body):
  lua,run=self.build(body);adapter=lua.execute((base.ROOT/'work/v05-parser/amalur_uint64.lua').read_text());lua.globals()['__amalur_uint64']=adapter
  return lua,run,adapter
 def test_exact_high_bit_payload_transport(self):
  for raw in ('0000000000000000','ffffffffffffffff','fedcba9876543210','0020000000000001'):
   with self.subTest(raw=raw):
    lua,run,adapter=self.setup(fn([ins(25,bx=0),ins(9,b=2)],stack=1,constants=[self.constant(raw)]))
    token=run();self.assertTrue(adapter['is'](token));self.assertEqual(adapter.hex(token),raw[:-1]+'b')
 def test_shared_adapter_interns_canonical_low_nibble(self):
  lua,run,adapter=self.setup(fn([ins(25,a=0,bx=0),ins(25,a=1,bx=1),ins(9,b=3)],stack=2,constants=[self.constant('123456789abcdef0'),self.constant('123456789abcdefa')]))
  self.assertTrue(lua.eval('function(f) local a,b=f(); return rawequal(a,b) end')(run))
 def test_engine_callback_receives_opaque_token(self):
  lua,run,adapter=self.setup(fn([ins(25,a=1,bx=0),ins(22,b=2),ins(9,b=0)],params=1,stack=2,constants=[self.constant('fffedcba98765430')]))
  callback=lua.eval('function(x) return type(x),__amalur_uint64.hex(x) end')
  self.assertEqual(run(callback),('userdata','fffedcba9876543b'))
 def test_missing_adapter_fails_explicitly(self):
  lua,run=self.build(fn([ins(25,bx=0),ins(9,b=2)],stack=1,constants=[self.constant('ffffffffffffffff')]))
  with self.assertRaisesRegex(LuaError,'adapter required'):run()
 def test_numeric_adapter_substitute_rejected(self):
  lua,run=self.build(fn([ins(25,bx=0),ins(9,b=2)],stack=1,constants=[self.constant('0000000000000010')]))
  lua.execute('__amalur_uint64={from_hex=function() return 16 end,is=function() return true end,hex=function() return "000000000000001b" end}')
  with self.assertRaisesRegex(LuaError,'Invalid.*adapter'):run()
 def test_id_arithmetic_remains_guarded(self):
  lua,run,adapter=self.setup(fn([ins(25,bx=0),ins(34,a=1,b=0,c=0),ins(9,a=1,b=2)],stack=2,constants=[self.constant('0000000000000010')]))
  with self.assertRaisesRegex(LuaError,'numeric|domain'):run()
 def test_raw_hex_is_preserved_in_ir(self):
  raw='fffffffffffffff0';ir,_=self.lift(fn([ins(25,bx=0),ins(9,b=2)],stack=1,constants=[self.constant(raw)]))
  self.assertEqual(ir['root_function']['instructions'][0]['uint64_constants'],[{'index':0,'serialized_hex':raw}])
 def test_float_only_payload_is_not_accepted(self):
  self.assertFalse(self.lift(fn([ins(25,bx=0),ins(9,b=2)],stack=1,constants=[{'type':'uint64','value':float(2**63)}]))[0]['root_function']['body_emittable'])
