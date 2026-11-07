import json
import hashlib
import math
import struct
import tempfile
import unittest
from pathlib import Path
from amalur_scene import SceneError,bake,parse_bytes,transform

def carrier(record=None,space_id=524859,slot=152,pointer=208,count=1):
    payload=bytearray(280)
    struct.pack_into('<I',payload,0,space_id)
    struct.pack_into('<II',payload,152,pointer,count)
    if record is None:
        record=bytearray(80)
        struct.pack_into('<3ff4f3f',record,4,10.,20.,30.,1.,0.,0.,0.,1.,1.,1.,1.)
        struct.pack_into('<IIIII',record,48,0,17,23,1,0)
        struct.pack_into('<II',record,72,17,1)
    payload[200:280]=record
    return struct.pack('<II',len(payload),4)+payload+struct.pack('<I',slot)

def mesh(variant='DATA_0.pak'):
    return {'complete_consumption':True,'tool':'opem-amalur-fab-stream-reader',
            'input_file':'C:/work/'+variant+'/17.fab_visual_data_streamable_bin',
            'input_sha256':'a'*64,'summary':{'vertices':3,'triangles_in_buffers':1},
            'vertex_buffers':[{'stride_bytes':48,'positions':[[0.,0.,0.],[1.,0.,0.],[0.,1.,0.]]}],
            'index_buffers':[{'indices':[0,1,2]}],'assemblies':[{'vertex_buffer':0,'index_buffer':0}]}

def bind_fixture(root):
    (root/'17').mkdir();(root/'DATA_0.pak').mkdir();(root/'fabs').mkdir()
    native=root/'DATA_0.pak/17.fab_bxml';native.write_bytes(b'synthetic FAB provenance')
    geometry=mesh();geometry['input_file']=str(native).replace('.fab_bxml','.fab_visual_data_streamable_bin')
    (root/'17/native-mesh.json').write_text(json.dumps(geometry),encoding='utf-8')
    report={'input_path':'flat-copies/17.fab_bxml','input_sha256':hashlib.sha256(native.read_bytes()).hexdigest(),
            'profile':'external-2018-FAB-skeleton-layout','status':'parsed-reference-profile',
            'native_layout_confirmed':False,'mesh_count':1,'mesh_descriptors':[{
                'bone_index':0,'static_bind_candidate':[2,0,0,100,0,3,0,200,0,0,4,300,0,0,0,1]}]}
    source=root/'fabs/17.json';source.write_text(json.dumps(report),encoding='utf-8')
    return geometry,report,source

class SceneTests(unittest.TestCase):
    def test_native_minus_eight_and_field_offsets(self):
        result=parse_bytes(carrier())
        self.assertEqual(result['array']['payload_offset'],200)
        record=result['placements'][0]
        self.assertEqual(record['file_offset'],208)
        self.assertEqual(record['position_xyz'],[10.,20.,30.])
        self.assertEqual(record['quaternion_xyzw'],[0.,0.,0.,1.])
        self.assertEqual(record['fab_id'],17)
        self.assertEqual(record['instance_id'],23)
    def test_wrong_space_identity(self):
        with self.assertRaises(SceneError):parse_bytes(carrier(space_id=1))
    def test_pointer_must_be_in_native_fixup_list(self):
        with self.assertRaises(SceneError):parse_bytes(carrier(slot=156))
    def test_array_range_must_fit(self):
        for pointer,count in [(7,1),(209,1),(208,2),(208,100001)]:
            with self.subTest(pointer=pointer,count=count),self.assertRaises(SceneError):
                parse_bytes(carrier(pointer=pointer,count=count))
    def test_transform_guard(self):
        data=carrier()
        for offset,value in [(208+4,float('inf')),(208+16,0.),(208+32,0.)]:
            edited=bytearray(data);struct.pack_into('<f',edited,offset,value)
            with self.subTest(offset=offset),self.assertRaises(SceneError):parse_bytes(bytes(edited))
    def test_diagnostic_transform_math_is_explicit(self):
        placement={'position_xyz':[10,20,30],'scale_xyz':[2,3,4],
                   'quaternion_xyzw':[0,0,math.sqrt(.5),math.sqrt(.5)]}
        transformed=transform([1,0,0],placement)
        self.assertEqual(transformed,(10.,22.,30.))
    def test_bake_omsc07_contract_and_bounds(self):
        scene=parse_bytes(carrier());scene['archive_variant']='DATA_0.pak'
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'17').mkdir()
            (root/'17/native-mesh.json').write_text(json.dumps(mesh()),encoding='utf-8')
            output=root/'scene.bin';report=bake(scene,root,output);data=output.read_bytes()
        self.assertEqual(data[:8],b'OMSC07\0\0')
        self.assertEqual(len(data),36+3*36)
        self.assertEqual(struct.unpack_from('<I',data,8)[0],3)
        self.assertEqual(struct.unpack_from('<6f',data,12),(10.,20.,30.,11.,21.,30.))
        self.assertEqual(struct.unpack_from('<6f',data,36),(10.,20.,30.,0.,0.,1.))
        self.assertEqual(report['geometry_placements_loaded'],1)
        self.assertFalse(report['partial'])
    def test_missing_geometry_cannot_be_silently_accepted(self):
        scene=parse_bytes(carrier())
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(SceneError):bake(scene,Path(directory),Path(directory)/'scene.bin')
    def test_initial_archive_is_allowed_but_patch_is_rejected(self):
        scene=parse_bytes(carrier())
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'17').mkdir();source=root/'17/native-mesh.json'
            source.write_text(json.dumps(mesh('initial_0.pak')),encoding='utf-8')
            self.assertEqual(bake(scene,root,root/'scene.bin')['mesh_inputs'][0]['archive_variant'],'initial_0.pak')
            source.write_text(json.dumps(mesh('patch_0.pak')),encoding='utf-8')
            with self.assertRaises(SceneError):bake(scene,root,root/'scene.bin')
    def test_partial_export_requires_explicit_choice_and_reports_omission(self):
        scene=parse_bytes(carrier());scene['unique_fab_ids'].append(999)
        other=dict(scene['placements'][0]);other.update(index=1,fab_id=999)
        scene['placements'].append(other);scene['placement_count']=2
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'17').mkdir()
            (root/'17/native-mesh.json').write_text(json.dumps(mesh()),encoding='utf-8')
            with self.assertRaises(SceneError):bake(scene,root,root/'scene.bin')
            result=bake(scene,root,root/'scene.bin',allow_partial=True)
        self.assertTrue(result['partial']);self.assertEqual(result['missing_fab_ids'],[999])
        self.assertEqual(result['geometry_placements_loaded'],1)
        self.assertEqual(result['geometry_placements_requested'],2)

    def test_fab_bind_applied_before_instance_placement(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);bind_fixture(root)
            result=bake(parse_bytes(carrier()),root,root/'scene.bin',fab_root=root/'fabs')
        self.assertEqual(result['bounds_min'],[110.,220.,330.])
        self.assertEqual(result['bounds_max'],[112.,223.,330.])
        self.assertIn('static FAB binding',result['geometry_mode'])
        self.assertFalse(result['mesh_inputs'][0]['fab_bind']['native_layout_confirmed'])

    def test_fab_hash_mismatch_is_fatal_even_for_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);_,report,source=bind_fixture(root)
            report['input_sha256']='0'*64;source.write_text(json.dumps(report),encoding='utf-8')
            with self.assertRaises(SceneError):bake(parse_bytes(carrier()),root,root/'scene.bin',True,root/'fabs')

    def test_bind_matrix_and_descriptor_mismatch_rejected(self):
        for change in ['nonfinite','nonaffine','count']:
            with self.subTest(change=change),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);_,report,source=bind_fixture(root)
                if change=='nonfinite':report['mesh_descriptors'][0]['static_bind_candidate'][0]=float('nan')
                elif change=='nonaffine':report['mesh_descriptors'][0]['static_bind_candidate'][12]=1
                else:report['mesh_count']=2
                source.write_text(json.dumps(report),encoding='utf-8')
                with self.assertRaises(SceneError):bake(parse_bytes(carrier()),root,root/'scene.bin',True,root/'fabs')

    def test_unsupported_bind_omits_entire_asset_only_when_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);geometry,report,source=bind_fixture(root)
            (root/'18').mkdir()
            geometry['input_file']=geometry['input_file'].replace('17.','18.')
            (root/'18/native-mesh.json').write_text(json.dumps(geometry),encoding='utf-8')
            (root/'DATA_0.pak/18.fab_bxml').write_bytes((root/'DATA_0.pak/17.fab_bxml').read_bytes())
            report['mesh_descriptors'][0].update(bone_index=-1,static_bind_candidate=None,static_bind_candidate_error='mesh has no mapped bone')
            (root/'fabs/18.json').write_text(json.dumps(report),encoding='utf-8')
            scene=parse_bytes(carrier());scene['unique_fab_ids'].append(18)
            scene['placements'].append(dict(scene['placements'][0],index=1,fab_id=18));scene['placement_count']=2
            with self.assertRaises(SceneError):bake(scene,root,root/'scene.bin',fab_root=root/'fabs')
            result=bake(scene,root,root/'scene.bin',True,root/'fabs')
        self.assertTrue(result['partial']);self.assertEqual(result['geometry_placements_loaded'],1)
        self.assertEqual(result['omitted_placements'][0]['fab_id'],18)
        self.assertEqual(result['unsupported_fab_bindings'][0]['unsupported_assemblies'][0]['reason'],'mesh has no mapped bone')

    def test_skinned_stride_is_unsupported_not_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);geometry,_,_=bind_fixture(root)
            geometry['vertex_buffers'][0]['stride_bytes']=56
            (root/'17/native-mesh.json').write_text(json.dumps(geometry),encoding='utf-8')
            with self.assertRaisesRegex(SceneError,'unsupported static FAB'):
                bake(parse_bytes(carrier()),root,root/'scene.bin',fab_root=root/'fabs')

if __name__=='__main__':unittest.main()
