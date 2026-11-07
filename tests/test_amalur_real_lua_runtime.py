"""Isolated mock execution of two hash-bound reconstructed real functions.

These validate selected branch paths and shared-cell bindings in generated Lua
5.1, not native Havok execution. SQ02 uses primitive mock player tokens; actual
game actor/userdata comparison remains outside this test's evidence.
"""
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'python-libs'))
sys.path.insert(0, str(ROOT / 'src'))
from lupa.lua51 import LUA_VERSION, LuaRuntime
from amalur_reconstruct import emit_function


class RealReconstructedFunctionRuntimeTests(unittest.TestCase):
    def runtime(self):
        self.assertEqual(tuple(LUA_VERSION), (5, 1))
        lua = LuaRuntime(unpack_returned_tuples=True, register_eval=False, register_builtins=False)
        lua.execute("debug.sethook(function() error('real fixture instruction budget exceeded') end, '', 100000)")
        lua.execute('io=nil; os=nil; python=nil; dofile=nil; loadfile=nil; require=nil; debug=nil')
        return lua

    def load_function(self, name, path, expected_sha, expected_words):
        env = 'AMALUR_CAPTURE_IR' if name == '1378937' else 'AMALUR_SQ02_IR'
        default = ROOT / 'outputs' / 'reconstruction-v03' / ('ayten.ir.json' if name == '1378937' else 'sq02.ir.json')
        document = json.loads(Path(os.environ.get(env, default)).read_text(encoding='utf-8-sig'))
        self.assertEqual(document['input_sha256'], expected_sha)
        fn = document['root_function']
        for child_index in path.split('/')[1:]:
            fn = fn['children'][int(child_index)]
        self.assertEqual(fn['path'], path)
        self.assertTrue(fn['body_emittable'], json.dumps(fn['unknowns']))
        # Anchor each obligation to the original instruction words, including
        # consumed paired-JMP/DATA words, independently of the emitter's labels.
        words = {}
        for row in fn['instructions']:
            words[row['pc']] = row['word_hex']
            words.update((m['pc'], m['word_hex']) for m in row.get('metadata_words', []))
        self.assertEqual([words[i] for i in range(len(words))], expected_words)
        source = 'local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable\nreturn ' + '\n'.join(emit_function(fn))
        self.assertNotIn('UNRESOLVED function', source)
        return source

    def ayten(self):
        source = self.load_function(
            '1378937', '0/3', '7b2e42ae82c455928006e923764ea9a32a50c479abd7a14402f9d7331ce8ea7c',
            ['08010000', '39000a00', 'aa000101', '8c000214', '86020401', '8c000000', '8c000000',
             '40000002', '86040502', '8c000000', '8c000000', '32000603', '04060101', '12020000'])
        lua = self.runtime()
        lua.execute('''
          events = {}
          QUEST = {set_stage = function(...)
            assert(select('#', ...) == 2, 'QUEST.set_stage argument count')
            events[#events+1] = {'set_stage', ...}
          end}
        ''')
        factory = lua.execute(source)
        cells = lua.eval("{[0]={value={quest='mock-quest-A'}}}")
        return lua, factory, cells

    def sq02(self):
        source = self.load_function(
            'sq02', '0/2', '88e5baf1fb05dae012799fe3ec5afb9e831a9444d22d0092b3db9880dc84bf8c',
            ['aa000003', '8c000114', '7e020203', '08020300', '39000a00', 'aa000303',
             '8c000414', '86060603', '8c000000', '8c000000', 'aa000704', '8c000814',
             '32000a05', '04040204', '32000b05', '04060103', '12020000'])
        lua = self.runtime()
        lua.execute('''
          events = {}
          get_player = function(...)
            assert(select('#', ...) == 0, 'get_player argument count')
            events[#events+1] = {'get_player'}
            return 'primitive-player-token'
          end
          QUEST_ID = function(...)
            assert(select('#', ...) == 1, 'QUEST_ID argument count')
            events[#events+1] = {'QUEST_ID', ...}
            return 'mock-SQ02-id'
          end
          QUEST = {set_stage = function(...)
            assert(select('#', ...) == 2, 'QUEST.set_stage argument count')
            events[#events+1] = {'set_stage', ...}
          end}
        ''')
        return lua, lua.execute(source)

    def test_ayten_matching_choice_uses_captured_quest_and_stage_ten(self):
        lua, factory, cells = self.ayten()
        callback = factory(cells)
        self.assertIsNone(callback(1))
        events = lua.globals().events
        self.assertEqual(len(events), 1)
        self.assertEqual([events[1][i] for i in range(1, 4)], ['set_stage', 'mock-quest-A', 10])

    def test_ayten_other_choice_does_not_read_missing_capture_or_api(self):
        lua, factory, cells = self.ayten()
        callback = factory(cells)
        cells[0].value = None
        lua.globals().QUEST = None
        for choice in [0, 2, -1, False, None]:
            with self.subTest(choice=choice):
                self.assertIsNone(callback(choice))
        self.assertEqual(len(lua.globals().events), 0)

    def test_ayten_callbacks_follow_replaced_shared_capture_cell(self):
        lua, factory, cells = self.ayten()
        first, second = factory(cells), factory(cells)
        first(1)
        cells[0].value = lua.eval("{quest='mock-quest-B'}")
        first(1)
        second(1)
        events = lua.globals().events
        self.assertEqual(len(events), 3)
        self.assertEqual([events[i][2] for i in range(1, 4)],
                         ['mock-quest-A', 'mock-quest-B', 'mock-quest-B'])
        self.assertEqual([events[i][3] for i in range(1, 4)], [10, 10, 10])

    def test_sq02_matching_primitive_player_calls_quest_lookup_then_stage(self):
        lua, callback = self.sq02()
        self.assertIsNone(callback(None, 'primitive-player-token', None))
        events = lua.globals().events
        self.assertEqual(len(events), 3)
        self.assertEqual([events[1][i] for i in range(1, 2)], ['get_player'])
        self.assertEqual([events[2][i] for i in range(1, 3)], ['QUEST_ID', 'SQ02'])
        self.assertEqual([events[3][i] for i in range(1, 4)], ['set_stage', 'mock-SQ02-id', 20])

    def test_sq02_different_primitive_player_skips_quest_api(self):
        lua, callback = self.sq02()
        lua.globals().QUEST = None
        lua.globals().QUEST_ID = None
        self.assertIsNone(callback(None, 'different-player-token', None))
        events = lua.globals().events
        self.assertEqual(len(events), 1)
        self.assertEqual(events[1][1], 'get_player')


if __name__ == '__main__':
    unittest.main(verbosity=2)
