"""Extract the selected DATA Gorhart scene's inferred static placements.

The carrier relocation is native-confirmed. The80-byte record field meanings
remain an explicitly inferred profile until its native consumers are traced.
The optional baker produces our diagnostic OMSC07 geometry interchange only.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import struct
from pathlib import Path
from amalur_blob import parse_bytes as parse_blob

SPACE_ID=524859
SPACE_SHA256='775fb38b3fd9ff67ed3181579e935c70b33bd6831ccebf744ce4b2f6cd590143'
ARRAY_SLOT=152
RECORD_BYTES=80
SCENE_MAGIC=b'OMSC07\0\0'
MAX_SCENE_BYTES=256*1024*1024
ALLOWED_MESH_ARCHIVES=frozenset({'DATA_0.pak','initial_0.pak'})
PLACEMENT_NATIVE_EVIDENCE={
    'fab_instance_constructor':{'function':'0x00dddde0','evidence_id':'ev_7c621e91fd50ecf2c9ceae1ba776b6ffd3e0eca2d81a8fc1d4667b06ca52c1a9',
                                'observation':'Resolves record+0x34(52) as the FAB resource and passes record+4 to the transform path.'},
    'transform_copy':{'function':'0x00ac5560','evidence_id':'ev_01248ca54ee41a82f132d012aa3e6ca12b2b5c8ef5149a9bb6e7eb17bbd77d9b',
                      'observation':'Copies45 bytes from the supplied transform object; component arithmetic is not established by copying.'},
}

class SceneError(ValueError):pass
def sha(data):return hashlib.sha256(data).hexdigest()
def f32(x):return struct.unpack('<f',struct.pack('<f',x))[0]

def parse_bytes(data,expected_space_id=SPACE_ID):
    blob=parse_blob(data)
    payload=data[8:8+blob['header']['payload_bytes']]
    if len(payload)<ARRAY_SLOT+8:raise SceneError('payload is too short for selected root array slot')
    space_id=struct.unpack_from('<I',payload,0)[0]
    if space_id!=expected_space_id:raise SceneError('space identity differs from selected profile')
    if ARRAY_SLOT not in {r['slot_payload_offset'] for r in blob['slots']}:
        raise SceneError('selected array pointer is absent from native relocation slots')
    raw_pointer,count=struct.unpack_from('<II',payload,ARRAY_SLOT)
    target=raw_pointer-8
    if count>100_000:raise SceneError('placement count exceeds selected-profile budget')
    if target<0 or target>len(payload) or count*RECORD_BYTES>len(payload)-target:
        raise SceneError('placement array exceeds payload span')
    records=[]
    for i in range(count):
        offset=target+i*RECORD_BYTES
        raw=payload[offset:offset+RECORD_BYTES]
        words=list(struct.unpack('<20I',raw))
        position=list(struct.unpack_from('<3f',raw,4))
        w=struct.unpack_from('<f',raw,16)[0]
        quaternion=list(struct.unpack_from('<4f',raw,20))
        scale=list(struct.unpack_from('<3f',raw,36))
        if not all(math.isfinite(x) for x in position+[w]+quaternion+scale):
            raise SceneError(f'nonfinite inferred transform at record{i}')
        if max(map(abs,position),default=0)>1e9:raise SceneError(f'position outside viewer domain at record{i}')
        norm2=sum(x*x for x in quaternion)
        if abs(norm2-1)>0.002:raise SceneError(f'inferred quaternion is not approximately unit at record{i}')
        if abs(w-1)>1e-5:raise SceneError(f'inferred position W differs from1 at record{i}')
        asset_id=words[13]
        records.append({'index':i,'payload_offset':offset,'file_offset':offset+8,'bytes':RECORD_BYTES,
            'raw_hex':raw.hex(),'raw_words_u32':words,
            'position_xyz':position,'position_w':w,'quaternion_xyzw':quaternion,
            'quaternion_norm_squared':norm2,'scale_xyz':scale,'flags_u32':words[12],
            'fab_id':asset_id,'instance_id':words[14],'repeated_fab_id':words[18],
            'repeated_fab_id_matches':words[18]==asset_id,
            'unknown_words':{str(j*4):words[j] for j in [0,15,16,17,19]}})
    return {'schema_version':1,'tool':'opem-amalur-selected-scene-reader',
        'profile':'DATA-space524859 inferred80-byte static-placement records',
        'source_sha256':sha(data),'source_bytes':len(data),'space_id':space_id,
        'carrier_native_evidence':blob['native_relocation'],
        'placement_native_evidence':PLACEMENT_NATIVE_EVIDENCE,
        'field_semantics_status':'FAB reference at+52 and transform block at+4 statically confirmed; component roles and transform arithmetic remain inferred',
        'array':{'slot_payload_offset':ARRAY_SLOT,'raw_pointer':raw_pointer,
                 'payload_offset':target,'file_offset':target+8,'count':count,'stride_bytes':RECORD_BYTES},
        'placement_count':count,'unique_fab_ids':sorted({r['fab_id'] for r in records}),'placements':records,
        'limitations':['Carrier relocation, FAB reference and transform block are statically confirmed; component roles and transform arithmetic remain inferred.',
                       'Only this static placement array is decoded. Dynamic objects, collision, materials, lighting and scripts are separate.',
                       'No patch archive is merged and game archive precedence is not inferred.']}

def parse_file(path,variant):
    path=Path(path)
    if variant!='DATA_0.pak':raise SceneError('this admitted scene profile explicitly selects DATA_0.pak')
    if path.name!='524859.space_bxml':raise SceneError('this profile is pinned to524859.space_bxml')
    data=path.read_bytes()
    if sha(data)!=SPACE_SHA256:raise SceneError('selected DATA scene hash differs from verified input')
    result=parse_bytes(data)
    if result['placement_count']!=79:raise SceneError('selected scene no longer has79 observed placements')
    result['input_file']=str(path);result['archive_variant']=variant
    return result

def transform(position,placement):
    # Diagnostic assumption: scale, then right-handed Hamilton xyzw rotation,
    # then translation. Kept separate so native proof can replace it directly.
    x,y,z=(position[i]*placement['scale_xyz'][i] for i in range(3))
    qx,qy,qz,qw=placement['quaternion_xyzw']
    tx=2*(qy*z-qz*y);ty=2*(qz*x-qx*z);tz=2*(qx*y-qy*x)
    rotated=(x+qw*tx+qy*tz-qz*ty,y+qw*ty+qz*tx-qx*tz,z+qw*tz+qx*ty-qy*tx)
    return tuple(f32(rotated[i]+placement['position_xyz'][i]) for i in range(3))

def bind_point(matrix,position):
    return tuple(sum(matrix[row*4+i]*position[i] for i in range(3))+matrix[row*4+3] for row in range(3))

def load_bind_profile(fab_root,key,mesh,archive_variant):
    """Validate selected provenance before admitting an external-reference bind.

    Unsupported profiles are reportable omissions; mismatched provenance and
    malformed matrices always fail, including when partial export is requested.
    """
    source=Path(fab_root)/f'{key}.json'
    if not source.is_file():return None,{'reason':'missing selected FAB report'}
    raw=source.read_bytes();report=json.loads(raw)
    stream_path=str(mesh.get('input_file',''))
    suffix='.fab_visual_data_streamable_bin'
    if not stream_path.endswith(suffix):raise SceneError(f'mesh{key} has unexpected native stream suffix')
    native=Path(stream_path[:-len(suffix)]+'.fab_bxml')
    parts=str(native).replace('\\','/').split('/')
    if native.name!=f'{key}.fab_bxml' or sorted(ALLOWED_MESH_ARCHIVES.intersection(parts))!=[archive_variant] or 'patch_0.pak' in parts:
        raise SceneError(f'FAB{key} provenance does not match selected mesh archive and asset')
    if not native.is_file() or sha(native.read_bytes())!=report.get('input_sha256'):
        raise SceneError(f'FAB{key} source unavailable or hash differs from selected report')
    receipt={'fab_json':str(source),'fab_json_sha256':sha(raw),'native_fab_sha256':report['input_sha256'],
             'native_fab_file':str(native),'report_input_path':report.get('input_path'),
             'native_layout_confirmed':report.get('native_layout_confirmed'),
             'profile':report.get('profile')}
    if report.get('profile')!='external-2018-FAB-skeleton-layout' or report.get('status')!='parsed-reference-profile':
        return None,dict(receipt,reason=report.get('unsupported_reason','unsupported FAB profile'))
    descriptors=report.get('mesh_descriptors',[])
    if report.get('mesh_count')!=len(mesh['assemblies']) or len(descriptors)!=len(mesh['assemblies']):
        raise SceneError(f'FAB{key} descriptor count does not match decoded mesh assemblies')
    matrices=[];unsupported=[]
    for index,(descriptor,assembly) in enumerate(zip(descriptors,mesh['assemblies'])):
        stride=mesh['vertex_buffers'][assembly['vertex_buffer']].get('stride_bytes')
        # These strides are static/unskinned in the external importer profile.
        # Native classification remains unconfirmed; skinned layouts are omitted.
        if stride not in {20,24,44,48,52}:
            unsupported.append({'assembly':index,'reason':f'vertex stride {stride} is not admitted as unskinned'});continue
        matrix=descriptor.get('static_bind_candidate')
        if descriptor.get('bone_index',-1)<0 or matrix is None:
            unsupported.append({'assembly':index,'reason':descriptor.get('static_bind_candidate_error') or 'mesh has no mapped bone'});continue
        if len(matrix)!=16 or not all(isinstance(v,(int,float)) and math.isfinite(v) for v in matrix):
            raise SceneError(f'FAB{key} assembly{index} has malformed bind matrix')
        if any(abs(matrix[12+i]-expected)>1e-6 for i,expected in enumerate([0,0,0,1])):
            raise SceneError(f'FAB{key} assembly{index} bind matrix is not affine')
        matrices.append(matrix)
    if unsupported:return None,dict(receipt,reason='asset omitted because at least one assembly has unsupported static binding',unsupported_assemblies=unsupported)
    return matrices,receipt

def bake(scene,mesh_root,path,allow_partial=False,fab_root=None):
    mesh_root=Path(mesh_root);path=Path(path)
    meshes={};inputs=[];missing=[];unsupported=[];binds={}
    for key in scene['unique_fab_ids']:
        source=mesh_root/str(key)/'native-mesh.json'
        if not source.is_file():missing.append(key);continue
        raw=source.read_bytes();mesh=json.loads(raw)
        if not mesh.get('complete_consumption') or mesh.get('tool')!='opem-amalur-fab-stream-reader':
            raise SceneError(f'mesh{key} is not a complete admitted geometry decode')
        source_parts=str(mesh.get('input_file','')).replace('\\','/').split('/')
        if 'patch_0.pak' in source_parts:
            raise SceneError(f'mesh{key} comes from a patch variant; this diagnostic does not merge patches')
        archive_variants=sorted(ALLOWED_MESH_ARCHIVES.intersection(source_parts))
        if len(archive_variants)!=1:
            raise SceneError(f'mesh{key} does not identify exactly one explicitly allowed DATA/initial archive')
        receipt={'fab_id':key,'archive_variant':archive_variants[0],'mesh_json':str(source),'mesh_json_sha256':sha(raw),
                 'native_stream_sha256':mesh['input_sha256'],'summary':mesh['summary']}
        if fab_root is not None:
            matrices,fab_receipt=load_bind_profile(fab_root,key,mesh,archive_variants[0])
            receipt['fab_bind']=fab_receipt
            if matrices is None:
                unsupported.append(dict(fab_receipt,fab_id=key));continue
            binds[key]=matrices
        meshes[key]=mesh;inputs.append(receipt)
    if missing and not allow_partial:raise SceneError('missing decoded meshes: '+','.join(map(str,missing)))
    if unsupported and not allow_partial:raise SceneError('unsupported static FAB bindings: '+','.join(str(row['fab_id']) for row in unsupported))
    vertices=bytearray();minimum=[math.inf]*3;maximum=[-math.inf]*3
    receipts=[];zero_area=0;vertex_count=0
    for placement in scene['placements']:
        key=placement['fab_id']
        if key not in meshes:continue
        mesh=meshes[key];before=vertex_count
        # Stable neutral object colors are a diagnostic aid, not game materials.
        seed=(key*1103515245+12345)&0xffffffff
        color=tuple(0.38+((seed>>shift)&63)/200 for shift in [0,8,16])
        for assembly_index,assembly in enumerate(mesh['assemblies']):
            vb=mesh['vertex_buffers'][assembly['vertex_buffer']]
            ib=mesh['index_buffers'][assembly['index_buffer']]
            local_positions=vb['positions']
            if key in binds:local_positions=[bind_point(binds[key][assembly_index],v) for v in local_positions]
            transformed=[transform(v,placement) for v in local_positions]
            indices=ib['indices']
            for i in range(0,len(indices),3):
                p0,p1,p2=(transformed[j] for j in indices[i:i+3])
                a=[p1[j]-p0[j] for j in range(3)];b=[p2[j]-p0[j] for j in range(3)]
                cross=(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
                length=math.sqrt(sum(v*v for v in cross))
                normal=tuple(v/length for v in cross) if length>1e-15 else (0.,0.,0.)
                if not length>1e-15:zero_area+=1
                for point in [p0,p1,p2]:
                    if not all(math.isfinite(v) and abs(v)<=1e9 for v in point):raise SceneError('baked position outside finite viewer domain')
                    vertex_count+=1
                    if 36+vertex_count*36>MAX_SCENE_BYTES:raise SceneError('baked scene exceeds256MiB viewer limit')
                    vertices+=struct.pack('<9f',*point,*normal,*color)
                    for axis in range(3):minimum[axis]=min(minimum[axis],point[axis]);maximum[axis]=max(maximum[axis],point[axis])
        receipts.append({'placement_index':placement['index'],'fab_id':key,'instance_id':placement['instance_id'],
                         'first_output_vertex':before,'output_vertices':vertex_count-before,'diagnostic_color':color})
    if not vertex_count:raise SceneError('no triangles available to bake')
    data=SCENE_MAGIC+struct.pack('<I6f',vertex_count,*minimum,*maximum)+vertices
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    omitted_ids=set(missing)|{row['fab_id'] for row in unsupported}
    omitted=[{'placement_index':p['index'],'fab_id':p['fab_id'],'instance_id':p['instance_id']} for p in scene['placements'] if p['fab_id'] in omitted_ids]
    return {'scope':'Authored diagnostic scene geometry from selected DATA placement records and decoded buffers.',
            'geometry_mode':'external-reference static FAB binding, then inferred scene placement' if fab_root else 'raw mesh diagnostic without FAB binding',
            'scene_file':str(path),'scene_sha256':sha(data),'scene_bytes':len(data),'format':'OMSC07 authored interchange',
            'vertices':vertex_count,'triangles':vertex_count//3,'bounds_min':minimum,'bounds_max':maximum,
            'source_scene_sha256':scene['source_sha256'],'archive_variant':scene.get('archive_variant'),
            'placement_transform':'inferred scale then Hamilton xyzw rotation then translation; native consumer confirmation pending',
            'geometry_placements_loaded':len(receipts),'geometry_placements_requested':scene['placement_count'],
            'missing_fab_ids':missing,'unsupported_fab_bindings':unsupported,'omitted_placements':omitted,
            'partial':bool(omitted_ids),'zero_area_triangles':zero_area,
            'colors':'invented stable diagnostic colors per model; not recovered materials',
            'normals':'computed flat face normals from transformed geometry; zero normals retained for degenerate triangles',
            'mesh_inputs':inputs,'placements':receipts,
            'limitations':['Unknown native assembly draw ranges may alter which portions/LODs should actually be drawn.',
                           'FAB bind transforms and unskinned stride classification follow the external 2018 reference; native confirmation remains pending.',
                           'Only the 79-record prop collection is represented; the room shell is not yet identified.',
                           'No material, texture, collision, animation, dynamic object, lighting or gameplay completeness claim.']}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('space',type=Path);parser.add_argument('--variant',required=True,choices=['DATA_0.pak'])
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--mesh-root',type=Path);parser.add_argument('--scene-bin',type=Path)
    parser.add_argument('--fab-root',type=Path,help='Selected FAB reports as ID.json; enables strict static bind application')
    parser.add_argument('--allow-partial',action='store_true')
    args=parser.parse_args();scene=parse_file(args.space,args.variant)
    if bool(args.mesh_root)!=bool(args.scene_bin):parser.error('--mesh-root and --scene-bin must be used together')
    if args.fab_root and not args.scene_bin:parser.error('--fab-root requires --scene-bin')
    if args.scene_bin:scene['baked_scene']=bake(scene,args.mesh_root,args.scene_bin,args.allow_partial,args.fab_root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(scene,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:scene[k] for k in ['source_sha256','space_id','archive_variant','placement_count','unique_fab_ids','array']},indent=2))
    if 'baked_scene' in scene:print(json.dumps({k:v for k,v in scene['baked_scene'].items() if k not in ['mesh_inputs','placements']},indent=2))

if __name__=='__main__':main()
