"""Hash-bound real loop/open-list functions, freshly reconstructed on Windows.

Mocks exercise the generated Lua 5.1 functions. They do not execute the native
Havok interpreter, actual actors, or game APIs. Input files are never modified.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'python-libs'))
sys.path.insert(0, str(ROOT / 'src'))
from lupa.lua51 import LUA_VERSION, LuaRuntime
from amalur_script import parse_file
from amalur_reconstruct import emit_function, reconstruct

MELEE_WORDS = [
    'aa000001', '8c000114', '0e000002', '04040201', '32000302', 'aa000403',
    '8c000514', '86060703', '8c000000', '8c000000', '0e020004', '04040203',
    '32000304', '71001402', 'aa000806', '8c000914', '860c0b06', '8c000000',
    '8c000000', '0e000007', '14020508', '8c000000', '8c000000', 'aa000809',
    '8c000914', '86120c09', '8c000000', '8c000000', '0e00000a', '04040009',
    '04000206', '02000006', '39000100', '1a020006', '12040006', '72ffe902',
    '1a000002', '12040002', '12020000',
]
GENERIC_WORDS = [
    'aa000000', '8c000114', '86000300', '8c000000', '8c000000', '32000401',
    '04040200', 'aa000501', '8c000614', '0e000002', '04040401', '39000600',
    'aa000006', '8c000114', '860c0806', '8c000000', '8c000000', '0e0a0007',
    '04040106', '1c000201', '38fff600', '12020000',
]
OPEN_WORDS = [
    'aa000000', '8c000114', '86000300', '8c000000', '8c000000',
    'aa000401', '8c000514', '7e020001', '04000100', '12020000',
]
AYTEN_WORDS = [
    '5c000001', '32000002', 'aa000103', '8c000214', '62060003', '32000004',
    '71001502', 'aa000406', '8c000514', '860c0706', '8c000000', '8c000000',
    'aa000107', '8c000214', '140e0507', '8c000000', '8c000000', '140c0706',
    '8c000000', '8c000000', '000c0801', '8c000000', '8c000000', '86020907',
    '8c000000', '8c000000', '080e0000', '39000000', '39000000', '72ffe802',
    '12040001', '12020000',
]


class RealLoopOpenListRuntimeTests(unittest.TestCase):
    def build(self, filename, sha, function_path, expected_words, corpus=True, sample_directory=None):
        sample_root = Path(sample_directory) if sample_directory is not None else Path(os.environ.get(
            'AMALUR_CAPTURE_SAMPLES' if corpus else 'AMALUR_SCRIPT_SAMPLES',
            ROOT / 'work' / ('capture-corpus' if corpus else 'script-samples')))
        path = sample_root / filename
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), sha)
        parsed = parse_file(path)
        self.assertEqual(parsed['input_sha256'], sha)
        original = parsed['chunk']['root_function']
        for index in function_path.split('/')[1:]:
            original = original['children'][int(index)]
        self.assertEqual([row['word_hex'] for row in original['instructions']], expected_words)
        profile_path = Path(os.environ.get('AMALUR_NATIVE_PROFILE', ROOT / 'outputs' / 'native-script-profile.json'))
        profile = json.loads(profile_path.read_text(encoding='utf-8-sig'))
        ir, _ = reconstruct(parsed, profile)
        function = ir['root_function']
        for index in function_path.split('/')[1:]:
            function = function['children'][int(index)]
        self.assertTrue(function['body_emittable'], json.dumps(function['unknowns'], indent=2))
        self.assertEqual(function['upvalue_count'], 0)
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), sha)
        self.assertEqual(tuple(LUA_VERSION), (5, 1))
        lua = LuaRuntime(unpack_returned_tuples=True, register_eval=False, register_builtins=False)
        lua.execute("debug.sethook(function() error('real loop/list instruction budget exceeded') end, '', 100000)")
        lua.execute('io=nil; os=nil; python=nil; dofile=nil; loadfile=nil; require=nil; debug=nil')
        header = 'local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable\nreturn '
        source = header + '\n'.join(emit_function(function))
        self.assertNotIn('UNRESOLVED function', source)
        return lua, lua.execute(source)

    def generic(self, populated):
        lua, run = self.build('1701254.lua_bxml',
                              '2a244641a49566fa00ec4805c5e1362f9f22dde3a4f4fea0831f61cb4a476295',
                              '0/3', GENERIC_WORDS, corpus=False)
        lua.execute('''
          events = {}; objects = {}
          GAME = {
            get_encounter_objects = function(...)
              assert(select('#', ...) == 1)
              assert((...) == 'ENC_Quest_SQ97_AltarEncounter')
              events[#events+1] = {'get', ...}
              return objects
            end,
            destroy_actor = function(...)
              assert(select('#', ...) == 1)
              events[#events+1] = {'destroy', ...}
            end
          }
          -- Exercise the generic iterator contract with a Lua mock, not a
          -- claim that Havok's specialized builtin iterator fastpath ran.
          ipairs = function(values)
            local function next_value(state, index)
              index = index + 1
              if state[index] ~= nil then return index, state[index] end
              return nil
            end
            return next_value, values, 0
          end
        ''')
        if populated:
            lua.execute("objects = {'actor-A', 'actor-B', 'actor-C'}")
        self.assertEqual(lua.eval("function(f) return select('#', f()) end")(run), 0)
        events = lua.globals().events
        return [[events[i][1], events[i][2]] for i in range(1, len(events) + 1)]

    def test_real_generic_loop_visits_all_encounter_objects_in_order(self):
        self.assertEqual(self.generic(True), [
            ['get', 'ENC_Quest_SQ97_AltarEncounter'],
            ['destroy', 'actor-A'], ['destroy', 'actor-B'], ['destroy', 'actor-C'],
        ])

    def test_real_generic_loop_skips_empty_encounter(self):
        self.assertEqual(self.generic(False), [['get', 'ENC_Quest_SQ97_AltarEncounter']])

    def melee(self, available, empty=False):
        lua, run = self.build('109574.lua_bxml',
                              'b08b37bfe2a3fc67633f4cdc88b460158770185485ed046368f7958ef6dc9d24',
                              '0/12', MELEE_WORDS)
        lua.execute('''
          events = {}; attacks = {'jab', 'slash', 'kick'}
          get_attacks_to_use = function(...)
            assert(select('#', ...) == 1 and (...) == 'actor-A')
            events[#events+1] = {'get_attacks', ...}
            return attacks
          end
          ACTOR = {
            get_suggested_target = function(...)
              assert(select('#', ...) == 1 and (...) == 'actor-A')
              events[#events+1] = {'target', ...}
              return 'target-A', nil
            end,
            is_talent_available = function(...)
              assert(select('#', ...) == 4, 'open target list must retain trailing nil')
              local actor, talent, target, trailing = ...
              assert(actor == 'actor-A' and target == 'target-A' and trailing == nil)
              events[#events+1] = {'available', talent}
              return talent == available_talent
            end
          }
        ''')
        lua.globals().available_talent = available
        if empty:
            lua.execute('attacks = {}')
        result = run('actor-A')
        events = lua.globals().events
        return result, [[events[i][1], events[i][2]] for i in range(1, len(events) + 1)]

    def test_real_numeric_loop_returns_early_on_available_talent(self):
        result, events = self.melee('slash')
        self.assertIs(result, True)
        self.assertEqual(events, [['get_attacks', 'actor-A'], ['target', 'actor-A'],
                                  ['available', 'jab'], ['target', 'actor-A'], ['available', 'slash']])

    def test_real_numeric_loop_exhausts_unavailable_talents(self):
        result, events = self.melee('none')
        self.assertIs(result, False)
        self.assertEqual(events, [['get_attacks', 'actor-A'], ['target', 'actor-A'],
                                  ['available', 'jab'], ['target', 'actor-A'], ['available', 'slash'],
                                  ['target', 'actor-A'], ['available', 'kick']])

    def test_real_numeric_loop_empty_attack_list_has_no_body_calls(self):
        result, events = self.melee('none', empty=True)
        self.assertIs(result, False)
        self.assertEqual(events, [['get_attacks', 'actor-A']])

    def test_real_open_call_forwards_zero_one_and_nil_bearing_results(self):
        for producer_source, expected in [
            ('function() end', []),
            ("function() return 'player-A' end", ['player-A']),
            ("function() return 'player-A', nil, 'extra', nil end", ['player-A', None, 'extra', None]),
        ]:
            with self.subTest(results=expected):
                lua, run = self.build('694583.lua_bxml',
                                      '93013038b03d7a0b19b642691e676b5af5993712827ff71379d41ac4abd59abb',
                                      '0/14', OPEN_WORDS)
                lua.globals().producer = lua.eval(producer_source)
                lua.execute('''
                  events = {}
                  get_player = function(...)
                    assert(select('#', ...) == 0)
                    events[#events+1] = {'get_player'}
                    return producer()
                  end
                  ACTOR = {stop_dialog = function(...)
                    events[#events+1] = {'stop_dialog'}
                    forwarded = {n=select('#', ...), ...}
                  end}
                ''')
                self.assertEqual(lua.eval("function(f) return select('#', f()) end")(run), 0)
                self.assertEqual([lua.globals().events[i][1] for i in range(1, 3)], ['get_player', 'stop_dialog'])
                forwarded = lua.globals().forwarded
                self.assertEqual([forwarded[i] for i in range(1, forwarded.n + 1)], expected)

    def ayten(self):
        lua, run = self.build('1378937.lua_bxml',
                              '7b2e42ae82c455928006e923764ea9a32a50c479abd7a14402f9d7331ce8ea7c',
                              '0/4', AYTEN_WORDS)
        lua.execute('''
          m_QUEST_LIST = {'quest-A', 'quest-B', 'quest-C'}
          boards = {{name='first', marker='A'}, {name='match', marker='B'}, {name='match', marker='C'}}
          package = {loaded={
            ['quest-A']={board_data=boards[1]},
            ['quest-B']={board_data=boards[2]},
            ['quest-C']={board_data=boards[3]}
          }}
        ''')
        return lua, run

    def test_real_ayten_lookup_returns_first_matching_board_identity(self):
        lua, run = self.ayten()
        self.assertTrue(lua.eval('rawequal')(run('match'), lua.globals().boards[2]))

    def test_real_ayten_lookup_returns_last_board_when_no_name_matches(self):
        lua, run = self.ayten()
        self.assertTrue(lua.eval('rawequal')(run('missing'), lua.globals().boards[3]))

    def test_real_ayten_empty_quest_list_returns_fresh_empty_table(self):
        lua, run = self.ayten()
        lua.execute('m_QUEST_LIST = {}')
        first, second = run('missing'), run('missing')
        count = lua.eval('function(t) local n=0; for k,v in pairs(t) do n=n+1 end; return n end')
        self.assertEqual(count(first), 0)
        self.assertEqual(count(second), 0)
        self.assertFalse(lua.eval('rawequal')(first, second))


if __name__ == '__main__':
    unittest.main(verbosity=2)
