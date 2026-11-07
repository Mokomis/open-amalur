import json
import math
import struct
import tempfile
import unittest
from pathlib import Path
from amalur_mesh import Limits, MeshError, export_obj, export_portable, parse_bytes

def fixture(positions=None,indices=None,stride=48,assembly=None,header_word0=48):
    positions=[(0.,0.,0.),(1.,0.,0.),(0.,1.,0.)] if positions is None else positions
    indices=[0,1,2] if indices is None else indices
    data=bytearray(struct.pack('<IIIIII',1,1,1,header_word0,stride,len(positions)))
    for p in positions:data+=struct.pack('<fff',*p)+b'\xab'*(stride-12)
    data+=struct.pack('<I',len(indices))
    for index in indices:data+=struct.pack('<H',index)
    data+=assembly if assembly is not None else struct.pack('<HHI11I',0,0,0,*range(11))
    return bytes(data)

class MeshTests(unittest.TestCase):
    def test_native_coordinates_and_unknown_bytes_preserved(self):
        data=fixture(header_word0=999)
        result=parse_bytes(data)
        self.assertEqual(result['summary']['triangles_in_buffers'],1)
        self.assertEqual(result['vertex_buffers'][0]['positions'][1],[1.,0.,0.])
        self.assertEqual(result['vertex_buffers'][0]['header_word0'],999)
        self.assertEqual(result['vertex_buffers'][0]['opaque_vertex_tail_hex'],'ab'*(36*3))
        self.assertEqual(result['assemblies'][0]['unknown_u32_at8'],list(range(11)))
        self.assertEqual(result['bytes_consumed'],len(data))
    def test_all_admitted_strides_keep_position_prefix(self):
        for stride in [20,24,44,48,52,56,60,64,68]:
            with self.subTest(stride=stride):
                self.assertEqual(parse_bytes(fixture(stride=stride))['summary']['vertices'],3)
    def test_unadmitted_stride_rejected(self):
        with self.assertRaises(MeshError):parse_bytes(fixture(stride=28))
    def test_nonfinite_position_rejected(self):
        for value in [float('nan'),float('inf'),-float('inf')]:
            with self.subTest(value=value),self.assertRaises(MeshError):
                parse_bytes(fixture(positions=[(value,0,0)]))
    def test_index_count_must_form_triangles(self):
        with self.assertRaises(MeshError):parse_bytes(fixture(indices=[0,1]))
    def test_triangle_index_bounds(self):
        for index in [3,65535]:
            with self.subTest(index=index),self.assertRaises(MeshError):parse_bytes(fixture(indices=[0,1,index]))
    def test_assembly_buffer_references_validated(self):
        for vb,ib in [(1,0),(0,1),(65535,0)]:
            with self.subTest(vb=vb,ib=ib),self.assertRaises(MeshError):
                parse_bytes(fixture(assembly=struct.pack('<HHI11I',vb,0,ib,*range(11))))
    def test_trailing_section_not_silently_discarded(self):
        with self.assertRaises(MeshError):parse_bytes(fixture()+b'\0'*4)
    def test_all_truncations_fail(self):
        data=fixture()
        for length in range(len(data)):
            with self.subTest(length=length),self.assertRaises(MeshError):parse_bytes(data[:length])
    def test_limits_precede_unbounded_reads(self):
        for limits in [Limits(max_bytes=1),Limits(max_buffers=0),Limits(max_assemblies=0),
                       Limits(max_vertices=2),Limits(max_indices=2)]:
            with self.subTest(limits=limits),self.assertRaises(MeshError):parse_bytes(fixture(),limits)
    def test_huge_count_is_rejected(self):
        with self.assertRaises(MeshError):parse_bytes(struct.pack('<III',0xffffffff,0xffffffff,0xffffffff))
    def test_empty_stream_profiles(self):
        self.assertEqual(parse_bytes(b'\0'*4)['header']['empty_profile'],'four-byte empty stream')
        self.assertEqual(parse_bytes(b'\0'*12)['summary']['vertices'],0)
    def test_portable_export_exact_geometry_and_lengths(self):
        mesh=parse_bytes(fixture())
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'mesh.ommesh'
            report=export_portable(mesh,path);data=path.read_bytes()
        self.assertEqual(data[:8],b'OMMESH1\0')
        self.assertEqual(struct.unpack_from('<III',data,8),(1,3,3))
        self.assertEqual(struct.unpack_from('<9f',data,20),(0,0,0,1,0,0,0,1,0))
        self.assertEqual(struct.unpack_from('<3I',data,56),(0,1,2))
        self.assertEqual(len(data),68)
        self.assertEqual(report['bytes'],68)
    def test_obj_preserves_original_winding(self):
        mesh=parse_bytes(fixture(indices=[2,1,0]))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'mesh.obj';export_obj(mesh,path);text=path.read_text()
        self.assertIn('f 3 2 1\n',text)
        self.assertIn('v 1 0 0\n',text)
    def test_source_offsets_match_raw_vertex_and_index_values(self):
        data=fixture();result=parse_bytes(data)
        vb=result['vertex_buffers'][0];ib=result['index_buffers'][0]
        self.assertEqual(struct.unpack_from('<fff',data,vb['data_file_offset']+48),(1.,0.,0.))
        self.assertEqual(struct.unpack_from('<HHH',data,ib['data_file_offset']),(0,1,2))

if __name__=='__main__':unittest.main()
