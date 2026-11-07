import copy,json,math,tempfile,unittest
from pathlib import Path
from amalur_shell import load_model,validate_geometry,render_pose
from amalur_scene import SceneError,sha

def fixture():
    record={'assembly':0,'parallel_assembly_count':1,'position_xyz':[10,20,30],
            'quaternion_xyzw':[0,0,0,1],'scale_xyz':[1,1,1],'sphere':[10,20,30,2]}
    model={'mesh':{'assemblies':[{'vertex_buffer':0,'index_buffer':0,'unknown_u32_at8':[18,1,4,1,0,3,0,0,3,0,0]}],
                   'vertex_buffers':[{'positions':[[0,0,0],[1,0,0],[0,1,0]],'stride_bytes':56}],
                   'index_buffers':[{'indices':[0,1,2]}]},
           'fab':{'mesh_descriptors':[{'remaps':[],'bone_index':0,'position_xyz_uninterpreted':[0,0,0],
                                      'unknown_four_floats':[0,2,0,0],
                                      'static_bind_candidate':[1,0,0,0,0,1,0,0,0,0,1,380,0,0,0,1]}]}}
    return record,model

class ShellTests(unittest.TestCase):
    def test_scaling_uses_descriptor_center_not_origin(self):
        record,model=fixture();record['scale_xyz']=[.5,.5,.5];record['sphere']=[11.,20.,30.,1.]
        model['fab']['mesh_descriptors'][0]['position_xyz_uninterpreted']=[1.,0.,0.]
        geometry,error=validate_geometry(record,model)
        self.assertIsNone(error);self.assertEqual(geometry['positions'][0],(10.5,20.,30.))
        self.assertEqual(geometry['measurement']['descriptor_center_error'],0)
    def test_render_quaternion_uses_one_conjugate_convention(self):
        record,_=fixture();record['quaternion_xyzw']=[0,0,math.sqrt(.5),math.sqrt(.5)]
        self.assertEqual(render_pose([1,0,0],record),(10.,19.,30.))
    def test_precomposed_pose_does_not_double_apply_bind(self):
        record,model=fixture();geometry,error=validate_geometry(record,model)
        self.assertIsNone(error);self.assertEqual(geometry['positions'][0],(10.,20.,30.))
        self.assertEqual(geometry['measurement']['vertices_outside_sphere_tolerance_0_1'],0)
    def test_wrong_center_and_radius_rejected(self):
        for field in ['center','radius']:
            record,model=fixture()
            if field=='center':record['sphere'][0]+=1
            else:record['sphere'][3]+=1
            with self.subTest(field=field):self.assertIsNone(validate_geometry(record,model)[0])
    def test_actual_vertices_must_fit_sphere(self):
        record,model=fixture();model['mesh']['vertex_buffers'][0]['positions'][1]=[3,0,0]
        geometry,error=validate_geometry(record,model)
        self.assertIsNone(geometry);self.assertIn('1 vertices exceed',error)
    def test_incompatible_counts_are_not_whole_buffer_draws(self):
        record,model=fixture();model['mesh']['assemblies'][0]['unknown_u32_at8'][3]=2
        self.assertIsNone(validate_geometry(record,model)[0])
        record,model=fixture();record['parallel_assembly_count']=2
        with self.assertRaises(SceneError):validate_geometry(record,model)
    def test_remaps_or_no_bone_are_unsupported(self):
        for change in ['remaps','bone_index']:
            record,model=fixture();model['fab']['mesh_descriptors'][0][change]=[{}] if change=='remaps' else -1
            with self.subTest(change=change):self.assertIsNone(validate_geometry(record,model)[0])
    def test_bad_indices_and_nonfinite_positions_fail(self):
        for change in ['index','position']:
            record,model=fixture()
            if change=='index':model['mesh']['index_buffers'][0]['indices'][0]=3
            else:model['mesh']['vertex_buffers'][0]['positions'][0][0]=float('nan')
            with self.subTest(change=change),self.assertRaises(SceneError):validate_geometry(record,model)
    def test_cross_archive_fab_requires_matching_actual_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'meshes/17').mkdir(parents=True);(root/'fabs').mkdir()
            (root/'native/initial_0.pak').mkdir(parents=True);(root/'native/DATA_0.pak').mkdir()
            native=root/'native/initial_0.pak/17.fab_visual_data_streamable_bin';native.write_bytes(b'mesh')
            nativefab=root/'native/DATA_0.pak/17.fab_bxml';nativefab.write_bytes(b'fab')
            _,model=fixture();mesh=model['mesh'];fab=model['fab']
            mesh.update(tool='opem-amalur-fab-stream-reader',complete_consumption=True,input_file=str(native),input_sha256=sha(b'mesh'))
            fab.update(status='parsed-reference-profile',profile='external-2018-FAB-skeleton-layout',mesh_count=1,input_sha256=sha(b'fab'))
            (root/'meshes/17/native-mesh.json').write_text(json.dumps(mesh),encoding='utf-8')
            (root/'fabs/17.json').write_text(json.dumps(fab),encoding='utf-8')
            selected,error=load_model(17,root/'meshes',root/'fabs',root/'native')
            self.assertIsNone(error);self.assertEqual(selected['provenance']['native_fab_matching_files'],[str(nativefab)])
            nativefab.write_bytes(b'changed')
            with self.assertRaises(SceneError):load_model(17,root/'meshes',root/'fabs',root/'native')

if __name__=='__main__':unittest.main()
