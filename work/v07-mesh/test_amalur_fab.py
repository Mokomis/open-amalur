import math,struct,unittest
from amalur_fab import FabError,Limits,parse_bytes,static_bind_matrix,transform_point

def trs(position=(0,0,0),quaternion=(0,0,0,1),scale=(1,1,1)):
    return struct.pack('<12f',*quaternion,*position,1,*scale,0)

def fixture(parents=(-1,0),bone_id=1,remap_ids=(),unknown_groups=False):
    n=len(parents);matrices=b''.join(trs(position=(10,0,0) if i==0 else (0,3,0)) for i in range(n))
    mtx_at=52;parent_at=mtx_at+len(matrices);hash_at=parent_at+n*2;definition_at=hash_at+n*4
    header=struct.pack('<7I6i',definition_at,0x45533033,definition_at,0,0,n,0,
                       mtx_at-28,parent_at-32,hash_at-36,0,0,0)
    if unknown_groups:
        definition=struct.pack('<4I',123,2,11,12)+struct.pack('<II',1,2)+bytes(24+9)+struct.pack('<3I',2,21,22)+struct.pack('<IH',1,31)
    else:definition=struct.pack('<5I',123,0,0,0,0)
    definition+=struct.pack('<I',1)
    descriptor=struct.pack('<7fI',99,88,77,0,0,0,0,len(remap_ids))
    descriptor+=b''.join(trs()+struct.pack('<i',index) for index in remap_ids)
    descriptor+=struct.pack('<2fi',0,0,bone_id)+bytes(25)
    return header+matrices+struct.pack('<'+'h'*n,*parents)+struct.pack('<'+'I'*n,*range(n))+definition+descriptor

def patch(data,offset,fmt,*values):
    b=bytearray(data);struct.pack_into('<'+fmt,b,offset,*values);return bytes(b)

class FabTests(unittest.TestCase):
    def test_basic_header_and_hierarchy(self):
        result=parse_bytes(fixture());self.assertEqual(result['mesh_count'],1);self.assertEqual(len(result['bones']),2)
        self.assertEqual(transform_point(static_bind_matrix(result,0,vertices_are_unskinned=True),(0,0,0)),[10,3,0])
        self.assertFalse(result['native_layout_confirmed'])
    def test_raw_mesh_position_is_not_added(self):
        result=parse_bytes(fixture());self.assertEqual(result['mesh_descriptors'][0]['position_xyz_uninterpreted'],[99,88,77])
        self.assertEqual(transform_point(result['mesh_descriptors'][0]['static_bind_candidate'],(1,2,3)),[11,5,3])
    def test_parent_order_is_not_assumed(self):
        result=parse_bytes(fixture(parents=(1,-1),bone_id=0))
        self.assertEqual(transform_point(result['bones'][0]['world_matrix_row_major'],(0,0,0)),[10,3,0])
    def test_self_parent_root_form(self):
        result=parse_bytes(fixture(parents=(0,0)))
        self.assertEqual(result['bones'][0]['root_form'],'self-index')
    def test_parent_cycle_rejected(self):
        with self.assertRaisesRegex(FabError,'cycle'):parse_bytes(fixture(parents=(1,0)))
    def test_parent_out_of_range(self):
        with self.assertRaisesRegex(FabError,'parent index'):parse_bytes(fixture(parents=(-1,2)))
    def test_negative_parent_not_root(self):
        with self.assertRaisesRegex(FabError,'parent index'):parse_bytes(fixture(parents=(-2,0)))
    def test_nonunit_quaternion_explicitly_unsupported(self):
        data=patch(fixture(),52,'4f',0,0,0,0);result=parse_bytes(data)
        self.assertIsNone(result['bones'][0]['world_matrix_row_major'])
        with self.assertRaisesRegex(ValueError,'parent transform'):static_bind_matrix(result,0,vertices_are_unskinned=True)
    def test_rotation_scale_and_translation(self):
        data=bytearray(fixture());data[52:100]=trs((10,0,0),(0,0,math.sqrt(.5),math.sqrt(.5)),(2,3,4))
        result=parse_bytes(bytes(data));point=transform_point(result['bones'][0]['world_matrix_row_major'],(1,0,0))
        self.assertAlmostEqual(point[0],10,places=5);self.assertAlmostEqual(point[1],2,places=5)
    def test_nonfinite_transform_rejected(self):
        with self.assertRaisesRegex(FabError,'nonfinite'):parse_bytes(patch(fixture(),52,'f',float('nan')))
    def test_header_truncation(self):
        with self.assertRaisesRegex(FabError,'header'):parse_bytes(bytes(23))
    def test_wrong_magic(self):
        with self.assertRaisesRegex(FabError,'magic'):parse_bytes(patch(fixture(),4,'I',0))
    def test_file_limit(self):
        with self.assertRaisesRegex(FabError,'byte limit'):parse_bytes(fixture(),Limits(max_file_bytes=30))
    def test_bone_count_limit(self):
        with self.assertRaisesRegex(FabError,'bone count'):parse_bytes(fixture(),Limits(max_bones=1))
    def test_relative_pointer_before_file(self):
        with self.assertRaisesRegex(FabError,'bounds'):parse_bytes(patch(fixture(),28,'i',-29))
    def test_relative_pointer_after_file(self):
        with self.assertRaisesRegex(FabError,'bounds'):parse_bytes(patch(fixture(),28,'i',2147483647))
    def test_transform_array_bounds(self):
        data=fixture()
        with self.assertRaisesRegex(FabError,'transform array'):parse_bytes(patch(data,28,'i',len(data)-28-1))
    def test_descriptor_absolute_pointer_bounds(self):
        with self.assertRaisesRegex(FabError,'bounds'):parse_bytes(patch(fixture(),8,'I',0xffffffff))
    def test_descriptor_tail_bounds(self):
        with self.assertRaisesRegex(FabError,'bounds'):parse_bytes(fixture()[:-1])
    def test_nested_unknown_groups_consumed_with_bounds(self):
        result=parse_bytes(fixture(unknown_groups=True));self.assertEqual(result['definition']['unknown_blocks'][0]['count'],2)
        self.assertEqual(result['mesh_count'],1)
    def test_remap_matrix_preserved(self):
        result=parse_bytes(fixture(remap_ids=(0,1)))
        remaps=result['mesh_descriptors'][0]['remaps'];self.assertEqual([x['bone_index'] for x in remaps],[0,1])
        self.assertEqual(remaps[0]['trs']['quaternion_xyzw'],[0,0,0,1])
    def test_remap_bone_range(self):
        with self.assertRaisesRegex(FabError,'remap bone'):parse_bytes(fixture(remap_ids=(2,)))
    def test_remap_count_limit(self):
        with self.assertRaisesRegex(FabError,'remap count'):parse_bytes(fixture(remap_ids=(0,1)),Limits(max_remaps_per_mesh=1))
    def test_total_remap_count_limit(self):
        with self.assertRaisesRegex(FabError,'total remap'):parse_bytes(fixture(remap_ids=(0,)),Limits(max_total_remaps=0))
    def test_missing_mesh_bone_is_explicitly_unsupported(self):
        result=parse_bytes(fixture(bone_id=-1));self.assertIsNone(result['mesh_descriptors'][0]['static_bind_candidate'])
        with self.assertRaisesRegex(ValueError,'no mapped bone'):static_bind_matrix(result,0,vertices_are_unskinned=True)
    def test_mesh_bone_range(self):
        with self.assertRaisesRegex(FabError,'mesh bone'):parse_bytes(fixture(bone_id=2))
    def test_static_application_requires_admitted_geometry(self):
        with self.assertRaisesRegex(ValueError,'unskinned'):static_bind_matrix(parse_bytes(fixture()),0)
    def test_zero_bones_preserved_as_unsupported(self):
        data=struct.pack('<6I',0,0x45533033,0,0,0,0);result=parse_bytes(data)
        self.assertEqual(result['status'],'unsupported-no-skeleton');self.assertIsNone(result['mesh_count'])
    def test_unknown_tail_remains_explicit(self):
        data=fixture();result=parse_bytes(data+b'abc')
        self.assertEqual(result['coverage']['uninterpreted_ranges'],[{'file_offset':len(data),'bytes':3}])
    def test_input_identity(self):
        result=parse_bytes(fixture());self.assertEqual(len(result['input_sha256']),64)
        self.assertEqual(result['coverage']['bytes_read'],len(fixture()))

if __name__=='__main__':unittest.main()
