"""Pinned complete-member regression for the 12 Windows batch containers."""
import hashlib
import os
from pathlib import Path
import unittest
from amalur_script import inspect_bundle_file, iter_bundle_file

EXPECTED = {'batch_12842.lua_bxml': {'sha256': '46743097f0e400df892f7fc233652d25a830d2803c2c7b010cc3d3e7e1953fce', 'member_count': 772, 'summary': {'functions': 9267, 'instructions': 440287, 'constants': 161879}}, 'batch_12842_duplicate0.lua_bxml': {'sha256': '46743097f0e400df892f7fc233652d25a830d2803c2c7b010cc3d3e7e1953fce', 'member_count': 772, 'summary': {'functions': 9267, 'instructions': 440287, 'constants': 161879}}, 'batch_13016.lua_bxml': {'sha256': '03b7e98f1858e6182a347eefdf5a0eaf9980a60190b3897d8b6833d590a151c7', 'member_count': 154, 'summary': {'functions': 2533, 'instructions': 102590, 'constants': 41054}}, 'batch_13016_duplicate0.lua_bxml': {'sha256': 'a5ace81d006d5a19d4fe6541161e2d5bb7caa4f0fea5940e7b502f09cb7fc23a', 'member_count': 326, 'summary': {'functions': 2875, 'instructions': 159463, 'constants': 52786}}, 'batch_13171.lua_bxml': {'sha256': '380b90d1cfa4d479aaebbfe6b75886c300e2425631d1e13c91dda21900a5924c', 'member_count': 7, 'summary': {'functions': 373, 'instructions': 17125, 'constants': 6390}}, 'batch_13171_duplicate0.lua_bxml': {'sha256': '380b90d1cfa4d479aaebbfe6b75886c300e2425631d1e13c91dda21900a5924c', 'member_count': 7, 'summary': {'functions': 373, 'instructions': 17125, 'constants': 6390}}, 'batch_1712701.lua_bxml': {'sha256': '7fed7719695e9203171f13948cf1f20df4ed5879b627204f269d91970f9d3a19', 'member_count': 589, 'summary': {'functions': 2215, 'instructions': 86879, 'constants': 37575}}, 'batch_1712701_duplicate0.lua_bxml': {'sha256': '7fed7719695e9203171f13948cf1f20df4ed5879b627204f269d91970f9d3a19', 'member_count': 589, 'summary': {'functions': 2215, 'instructions': 86879, 'constants': 37575}}, 'batch_557499.lua_bxml': {'sha256': 'a046095c5bb60939784f0040284fb8f520803483424a3f49012edec32bb1fea6', 'member_count': 38, 'summary': {'functions': 618, 'instructions': 20403, 'constants': 8715}}, 'batch_557499_duplicate0.lua_bxml': {'sha256': 'a046095c5bb60939784f0040284fb8f520803483424a3f49012edec32bb1fea6', 'member_count': 38, 'summary': {'functions': 618, 'instructions': 20403, 'constants': 8715}}, 'batch_589925.lua_bxml': {'sha256': 'baadd3f612888a03695039afa17b442481870372a778996bffaab0c63392e1b2', 'member_count': 1539, 'summary': {'functions': 10737, 'instructions': 383319, 'constants': 160454}}, 'batch_589925_duplicate0.lua_bxml': {'sha256': 'baadd3f612888a03695039afa17b442481870372a778996bffaab0c63392e1b2', 'member_count': 1539, 'summary': {'functions': 10737, 'instructions': 383319, 'constants': 160454}}}

@unittest.skipUnless(os.name == 'nt', 'real game artifact tests run only on Windows')
class RealBatchTests(unittest.TestCase):
    def test_all_twelve_containers_and_every_member(self):
        source=Path.home()/'Documents'/'Opem Amalur'/'work'/'initial-script-corpus-v04'
        seen=0
        for name,expected in EXPECTED.items():
            with self.subTest(file=name):
                path=source/name
                self.assertTrue(path.exists(), str(path))
                before=hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(before,expected['sha256'])
                directory=inspect_bundle_file(path)
                self.assertEqual(directory['member_count'],expected['member_count'])
                self.assertEqual(directory['container_bytes_consumed'],path.stat().st_size)
                totals=dict.fromkeys(('functions','instructions','constants'),0)
                count=0
                for member in iter_bundle_file(path):
                    entry=directory['directory'][count]
                    self.assertEqual(member['input_sha256'],entry['member_sha256'])
                    self.assertEqual(member['container']['input_sha256'],before)
                    self.assertEqual(member['container']['index'],count)
                    self.assertEqual(member['container']['resource_id'],entry['resource_id'])
                    self.assertGreaterEqual(member['wrapper']['payload_file_offset'],entry['member_file_offset'])
                    self.assertEqual(member['chunk']['payload_bytes_consumed'],member['wrapper']['declared_payload_bytes'])
                    for key,value in member['chunk']['summary'].items():totals[key]+=value
                    count+=1
                self.assertEqual(count,expected['member_count'])
                self.assertEqual(totals,expected['summary'])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)
                seen+=count
        self.assertEqual(seen,6370)

if __name__=='__main__':unittest.main(verbosity=2)
