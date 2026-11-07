"""Validate the parser against a complete native-reader capture and live counterpart."""
from pathlib import Path
import hashlib,json,sys,unittest
ROOT=Path.home()/'Documents/Opem Amalur'
sys.path[:0]=[str(ROOT/'work/v07-bxml'),str(ROOT/'work/v13-properties')]
from compiled_type import CompiledTypeError
from native_type_catalog import decode_type

class RealWorkbenchTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw=(ROOT/'work/v15-properties/native-workbench-230417.bin').read_bytes()
  cls.proof=json.loads((ROOT/'outputs/scene-v15/native-workbench-decoded.json').read_text())
  parts=json.loads((ROOT/'outputs/scene-v13/component-map.json').read_text())['components']
  cls.names={p['kind']:p['tables'][0]['name'] for p in parts}

 def test_real_native_reader_input(self):
  self.assertEqual(len(self.raw),408)
  self.assertEqual(hashlib.sha256(self.raw).hexdigest(),'3aaa675201631ed6a3c27f15db2ed41cb0c317963f914acd2afd17822f55cbf7')
  decoded=decode_type(self.raw,self.names)
  native=self.proof['native_snapshot']
  self.assertEqual(decoded['parent_key_u32'],native['parent_source_key'])
  self.assertEqual(decoded['script_key_u32'],native['script_source_key'])
  self.assertEqual([p['kind'] for p in decoded['components']],[p['kind'] for p in native['parts']])
  interaction=next(p for p in decoded['components'] if p['kind']==34)
  self.assertEqual(interaction['reference_keys_u32'],[198236])
  self.assertEqual([x['native_instance_offset'] for x in interaction['native_property_copies']],[0x24,0x30,0x34,0x38,0x3c,0x40])
  self.assertEqual(interaction['native_property_copies'][1]['raw_hex'],'00004040')
  self.assertEqual(hashlib.sha256(self.raw).hexdigest(),self.proof['capture_sha256'])

 def test_compact_source_is_kept_distinct(self):
  raw=(ROOT/'work/v14-sol/real-inputs/230417.simtype_bxml').read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),'502a854c3f09c5226468542c3c0d0ea2c85bd28b0435bd93c3dd99523e024207')
  with self.assertRaisesRegex(CompiledTypeError,'compact SimType conversion is unresolved'):
   decode_type(raw,self.names)

if __name__=='__main__':unittest.main()
