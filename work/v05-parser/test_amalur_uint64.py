"""Windows Lua 5.1 carrier checks; no native engine execution or equivalence claim."""
import os
from pathlib import Path
import sys
import unittest

ROOT=Path.home()/'Documents'/'Opem Amalur'
sys.path.insert(0,str(ROOT/'tools'/'python-libs'))
from lupa.lua51 import LUA_VERSION, LuaError, LuaRuntime

SOURCE=(Path(__file__).resolve().parent/'amalur_uint64.lua').read_text(encoding='utf-8')

@unittest.skipUnless(os.name=='nt','all runtime tests run on Windows')
class OpaqueUint64RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(tuple(LUA_VERSION),(5,1))
        self.lua=LuaRuntime(unpack_returned_tuples=True,register_eval=False,register_builtins=False)
        self.lua.execute("debug.sethook(function() error('carrier instruction budget exceeded') end,'',100000)")
        self.lua.execute('io=nil; os=nil; python=nil; dofile=nil; loadfile=nil; require=nil; debug=nil')
        self.lua.globals().u64=self.lua.execute(SOURCE)

    def test_exact_bytes_and_canonical_low_nibble(self):
        self.lua.execute('''
          for _, raw in ipairs({'0000000000000000','123456789abcdef0',
                                'ffffffffffffffff','8000000000000000'}) do
            assert(u64.hex(u64.from_hex(raw)) == raw:sub(1,15)..'b')
          end
          assert(u64.hex(u64.from_hex('ABCDEF0123456789')) == 'abcdef012345678b')
        ''')

    def test_all_sixteen_serialized_low_nibbles_intern_together(self):
        self.lua.execute('''
          local base=u64.from_hex('0123456789abcde0')
          for i=1,16 do
            local raw='0123456789abcde'..('0123456789abcdef'):sub(i,i)
            assert(rawequal(base,u64.from_hex(raw)))
          end
        ''')

    def test_high_bits_and_adjacent_canonical_values_remain_distinct(self):
        self.lua.execute('''
          local a=u64.from_hex('ffffffffffffff0b')
          local b=u64.from_hex('ffffffffffffff1b')
          local c=u64.from_hex('7fffffffffffff0b')
          assert(not rawequal(a,b) and not rawequal(a,c))
          assert(u64.hex(a)=='ffffffffffffff0b' and u64.hex(b)=='ffffffffffffff1b')
        ''')

    def test_input_validation_rejects_implicit_numeric_conversion(self):
        self.lua.execute('''
          for _,value in ipairs({0,1,true,{},'', '0', '00000000000000000',
              '0x00000000000000','000000000000000g','000000000000000 '}) do
            assert(not pcall(u64.from_hex,value))
          end
          assert(not pcall(u64.from_hex,nil))
        ''')

    def test_userdata_is_immutable_and_metatable_is_hidden(self):
        self.lua.execute('''
          local token=u64.from_hex('123456789abcdef0')
          assert(type(token)=='userdata' and type(getmetatable(token))=='string')
          assert(not pcall(function() token.hex='changed' end))
          assert(not pcall(function() rawset(token,'hex','changed') end))
          assert(not pcall(function() setmetatable(token,{}) end))
          assert(u64.hex(token)=='123456789abcdefb')
        ''')

    def test_private_brand_rejects_foreign_and_metatable_cloned_userdata(self):
        self.lua.execute('''
          local token=u64.from_hex('0000000000000000')
          assert(u64.is(token) and not u64.is({}) and not u64.is(nil))
          local clone=newproxy(token)
          assert(not u64.is(clone) and not u64.is(newproxy(true)))
          assert(not pcall(u64.hex,clone) and not pcall(u64.hex,'000000000000000b'))
        ''')

    def test_zero_payload_is_truthy_and_not_a_number(self):
        self.lua.execute('''
          local token=u64.from_hex('0000000000000000')
          assert(token and not not token and tonumber(token)==nil)
          assert(token~=0 and token~='000000000000000b')
        ''')

    def test_no_arithmetic_ordering_or_concatenation_metamethods(self):
        self.lua.execute('''
          local token=u64.from_hex('0000000000000000')
          for _,operation in ipairs({function() return token+1 end,
              function() return token<token end,function() return token..'' end,
              function() return -token end,function() return #token end}) do
            assert(not pcall(operation))
          end
        ''')

    def test_transport_capture_return_and_plain_table_storage(self):
        self.lua.execute('''
          local token=u64.from_hex('123456789abcdef0')
          local function closure(value) return function() return value end end
          local callback=closure(token)
          local values={token}
          assert(rawequal(callback(),values[1]))
          local keys={[token]='value'}
          assert(keys[u64.from_hex('123456789abcdef1')]=='value')
          -- This only checks carrier interning under Lua; native key lookup remains unproven.
        ''')

    def test_adapter_receives_exact_tagged_bits_and_rejects_untyped_ids(self):
        self.lua.execute('''
          local events={}
          local function binding(id)
            assert(u64.is(id),'typed ID required')
            events[#events+1]={tag=11,canonical_bits_hex=u64.hex(id)}
          end
          binding(u64.from_hex('fedcba9876543210'))
          assert(events[1].tag==11 and events[1].canonical_bits_hex=='fedcba987654321b')
          assert(not pcall(binding,123) and not pcall(binding,'fedcba987654321b'))
        ''')

    def test_separate_runtime_instances_do_not_share_brands(self):
        self.lua.globals().other=self.lua.execute(SOURCE)
        self.lua.execute('''
          local foreign=other.from_hex('0000000000000000')
          assert(not u64.is(foreign) and not pcall(u64.hex,foreign))
        ''')

    def test_missing_newproxy_fails_instead_of_degrading_to_table_or_number(self):
        self.lua.execute('newproxy=nil')
        with self.assertRaisesRegex(LuaError,'requires Lua 5.1 newproxy'):
            self.lua.execute(SOURCE)

if __name__=='__main__':unittest.main(verbosity=2)
