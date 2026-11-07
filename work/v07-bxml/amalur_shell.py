"""Measured static-shell candidate from the selected scene's primary render set.

This is a diagnostic reconstruction, not native-renderer equivalence. It admits
one assembly per uniquely matched center and validates its geometry against the
stored sphere. Additional LOD/render sets are deliberately not drawn.
"""
from __future__ import annotations
import argparse,hashlib,json,math,struct
from pathlib import Path
from amalur_blob import parse_bytes as parse_blob
from amalur_scene import SPACE_SHA256,SCENE_MAGIC,MAX_SCENE_BYTES,SceneError,transform,sha

def finite(values):return all(isinstance(v,(int,float)) and math.isfinite(v) for v in values)
def distance(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
def render_pose(position,record,center=(0.,0.,0.)):
    # One convention for every record: measured across151 selected assemblies.
    # Conjugation includes all41 direct passes and71 additional passes. Scaling
    # about the descriptor center additionally resolves all39 scaled residuals;
    # the expanded selected corpus passes the same gates for172/172 records.
    q=record['quaternion_xyzw']
    local=[center[i]+(position[i]-center[i])*record['scale_xyz'][i] for i in range(3)]
    return transform(local,dict(record,quaternion_xyzw=[-q[0],-q[1],-q[2],q[3]],scale_xyz=[1.,1.,1.]))

def selected_records(data):
    if sha(data)!=SPACE_SHA256:raise SceneError('shell profile requires verified DATA scene524859')
    blob=parse_blob(data);size=blob['header']['payload_bytes'];slots={s['slot_payload_offset'] for s in blob['slots']}
    def array(slot,stride):
        if slot not in slots:raise SceneError('required pointer is not relocated')
        target,count=struct.unpack_from('<II',data,8+slot)
        if count>100000 or target<8 or target+count*stride>size+8:raise SceneError('shell array span invalid')
        return [(target+i*stride,data[target+i*stride:target+(i+1)*stride]) for i in range(count)]
    ids=[struct.unpack('<I',r)[0] for _,r in array(0x118,4)]
    counts=[struct.unpack('<I',r)[0] for _,r in array(0x120,4)]
    if len(ids)!=len(counts) or len(set(ids))!=len(ids):raise SceneError('FAB list/count ambiguity')
    expected=dict(zip(ids,counts));refs=array(0x1b0,4);centers=array(0x1a8,12);renders=array(0x160,84)
    if len(refs)!=172 or len(centers)!=len(refs) or len(renders)!=len(refs):raise SceneError('primary array counts differ from observed profile')
    sphere_centers=[struct.unpack_from('<3f',r) for _,r in renders];used=set();result=[]
    for index,((reference_at,rawref),(_,rawcenter)) in enumerate(zip(refs,centers)):
        typed=struct.unpack('<I',rawref)[0];fab=typed&0xfffffff;center=struct.unpack('<3f',rawcenter)
        if typed>>28!=15 or fab not in expected or not finite(center):raise SceneError('typed FAB or center profile mismatch')
        matches=[i for i,c in enumerate(sphere_centers) if finite(c) and distance(center,c)<.01]
        if len(matches)!=1 or matches[0] in used:raise SceneError('primary sphere permutation is not one-to-one')
        match=matches[0];used.add(match);at,raw=renders[match]
        position=list(struct.unpack_from('<4f',raw,16));quaternion=list(struct.unpack_from('<4f',raw,32));scale=list(struct.unpack_from('<3f',raw,48))
        sphere=list(struct.unpack_from('<4f',raw));assembly=struct.unpack_from('<I',raw,68)[0]
        if assembly>=expected[fab] or not finite(position+quaternion+scale+sphere):raise SceneError('render record outside admitted domain')
        if abs(position[3]-1)>.00001 or abs(sum(q*q for q in quaternion)-1)>.002 or sphere[3]<=0:raise SceneError('render pose/sphere profile mismatch')
        result.append({'reference_index':index,'reference_file_offset':reference_at,'typed_reference':typed,'fab_id':fab,
            'render_index':match,'render_file_offset':at,'raw_render_hex':raw.hex(),'parallel_assembly_count':expected[fab],
            'assembly':assembly,'material_id_candidate':struct.unpack_from('<I',raw,64)[0],
            'position_xyz':position[:3],'quaternion_xyzw':quaternion,'scale_xyz':scale,'sphere':sphere,
            'center_match_distance':distance(center,sphere[:3])})
    return result,blob['native_relocation']

def load_model(key,mesh_root,fab_root,native_root):
    mp=Path(mesh_root)/str(key)/'native-mesh.json';fp=Path(fab_root)/f'{key}.json'
    if not mp.is_file() or not fp.is_file():return None,'missing selected mesh or FAB report'
    mr=mp.read_bytes();fr=fp.read_bytes();mesh=json.loads(mr);fab=json.loads(fr)
    if mesh.get('tool')!='opem-amalur-fab-stream-reader' or not mesh.get('complete_consumption'):
        raise SceneError('mesh is not a complete admitted decode')
    native=Path(mesh.get('input_file',''));parts=str(native).replace('\\','/').split('/')
    if native.name!=f'{key}.fab_visual_data_streamable_bin' or 'patch_0.pak' in parts or sum(p in parts for p in ['DATA_0.pak','initial_0.pak'])!=1:
        raise SceneError('native stream provenance outside selected DATA/initial scope')
    if not native.is_file() or sha(native.read_bytes())!=mesh.get('input_sha256'):raise SceneError('native mesh source/hash mismatch')
    matches=[]
    for archive in ['DATA_0.pak','initial_0.pak']:
        candidate=Path(native_root)/archive/f'{key}.fab_bxml'
        if candidate.is_file() and sha(candidate.read_bytes())==fab.get('input_sha256'):matches.append(str(candidate))
    if not matches:raise SceneError('no selected original FAB matches report hash')
    if fab.get('status')!='parsed-reference-profile' or fab.get('profile')!='external-2018-FAB-skeleton-layout':return None,'unsupported FAB descriptor profile'
    if len(mesh['assemblies'])!=fab.get('mesh_count') or len(fab['mesh_descriptors'])!=fab['mesh_count']:
        raise SceneError('FAB/stream assembly count mismatch')
    return {'mesh':mesh,'fab':fab,'provenance':{'fab_id':key,'mesh_json':str(mp),'mesh_json_sha256':sha(mr),
        'fab_json':str(fp),'fab_json_sha256':sha(fr),'native_mesh_file':str(native),'native_mesh_sha256':mesh['input_sha256'],
        'native_fab_matching_files':matches,'native_fab_sha256':fab['input_sha256']}},None

def validate_geometry(record,model):
    mesh=model['mesh'];fab=model['fab'];index=record['assembly']
    if record['parallel_assembly_count']!=len(mesh['assemblies']):raise SceneError('root assembly count differs from selected model')
    assembly=mesh['assemblies'][index];desc=fab['mesh_descriptors'][index]
    if desc.get('remaps') or desc.get('bone_index',-1)<0:return None,'descriptor has remaps or lacks mapped bone'
    vb=mesh['vertex_buffers'][assembly['vertex_buffer']];ib=mesh['index_buffers'][assembly['index_buffer']]
    positions=vb['positions'];indices=ib['indices']
    if not positions or not indices or len(indices)%3 or any(not isinstance(i,int) or i<0 or i>=len(positions) for i in indices):raise SceneError('triangle index domain invalid')
    if any(len(p)!=3 or not finite(p) for p in positions):raise SceneError('vertex position is not finite xyz')
    words=assembly['unknown_u32_at8']
    if len(words)!=11 or words[3]!=len(indices)//3 or words[5]!=len(indices) or words[8]!=len(positions):
        return None,'native assembly count words do not match complete buffers'
    center=desc['position_xyz_uninterpreted']
    sphere=record['sphere'];predicted=render_pose(center,record,center)
    error=distance(predicted,sphere[:3]);radius=desc['unknown_four_floats'][1]*max(map(abs,record['scale_xyz']))
    if not finite([radius,error]) or error>.01 or abs(radius-sphere[3])>max(.01,sphere[3]*1e-5):
        return None,'descriptor center/radius does not match precomposed scene pose'
    transformed=[render_pose(p,record,center) for p in positions]
    distances=[distance(p,sphere[:3]) for p in transformed]
    if any(not finite(p) or max(map(abs,p))>1e9 for p in transformed):raise SceneError('transformed vertex outside finite domain')
    outside=sum(d>sphere[3]+.1 for d in distances)
    if outside:return None,f'{outside} vertices exceed stored sphere plus0.1 tolerance'
    return {'positions':transformed,'indices':indices,'measurement':{'descriptor_center_error':error,
        'radius_error':abs(radius-sphere[3]),'maximum_vertex_distance':max(distances),'sphere_radius':sphere[3],
        'vertices_outside_sphere_tolerance_0_1':outside,'stride_bytes':vb['stride_bytes']}},None

def bake(data,mesh_root,fab_root,native_root,path,allow_partial=False):
    records,evidence=selected_records(data);models={};missing={};inputs=[]
    for key in sorted({r['fab_id'] for r in records}):
        model,error=load_model(key,mesh_root,fab_root,native_root)
        if error:missing[key]=error
        else:models[key]=model;inputs.append(model['provenance'])
    vertices=bytearray();minimum=[math.inf]*3;maximum=[-math.inf]*3;admitted=[];omitted=[];zero_area=0
    for record in records:
        key=record['fab_id'];geometry=None;error=missing.get(key)
        if error is None:geometry,error=validate_geometry(record,models[key])
        if error:
            omitted.append({'reference_index':record['reference_index'],'render_index':record['render_index'],'fab_id':key,'assembly':record['assembly'],'reason':error});continue
        before=len(vertices)//36;positions=geometry['positions'];indices=geometry['indices']
        seed=(key*1103515245+12345)&0xffffffff;color=tuple(.38+((seed>>shift)&63)/200 for shift in [0,8,16])
        for i in range(0,len(indices),3):
            points=[positions[j] for j in indices[i:i+3]];a=[points[1][j]-points[0][j] for j in range(3)];b=[points[2][j]-points[0][j] for j in range(3)]
            cross=(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]);length=math.sqrt(sum(v*v for v in cross))
            normal=tuple(v/length for v in cross) if length>1e-15 else (0.,0.,0.)
            if length<=1e-15:zero_area+=1
            if len(vertices)+3*36+36>MAX_SCENE_BYTES:raise SceneError('candidate exceeds viewer size budget')
            for point in points:
                vertices+=struct.pack('<9f',*point,*normal,*color)
                for axis in range(3):minimum[axis]=min(minimum[axis],point[axis]);maximum[axis]=max(maximum[axis],point[axis])
        admitted.append(dict(record,first_output_vertex=before,output_vertices=len(vertices)//36-before,measurement=geometry['measurement']))
    if omitted and not allow_partial:raise SceneError(f'{len(omitted)} primary records unsupported; --allow-partial required')
    if not vertices:raise SceneError('no validated geometry to bake')
    binary=SCENE_MAGIC+struct.pack('<I6f',len(vertices)//36,*minimum,*maximum)+vertices
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(binary)
    return {'tool':'opem-amalur-measured-shell-candidate','source_scene_sha256':sha(data),'native_carrier_evidence':evidence,
        'scene_file':str(path),'scene_sha256':sha(binary),'scene_bytes':len(binary),'vertices':len(vertices)//36,
        'triangles':len(vertices)//108,'bounds_min':minimum,'bounds_max':maximum,'zero_area_triangles':zero_area,
        'primary_records_requested':len(records),'primary_records_loaded':len(admitted),'partial':bool(omitted),
        'model_inputs':inputs,'admitted_records':admitted,'omitted_records':omitted,
        'scope':'Measured diagnostic static assemblies using precomposed84-byte scene poses; no extra FAB bind applied.',
        'rotation_convention':'Conjugated stored xyzw quaternion consistently for all records; measured against descriptor centers and actual vertex enclosure.',
        'scale_convention':'Scale consistently about the selected FAB descriptor center, then conjugate rotation and translation; measured for172 selected records.',
        'excluded_sets':['root+0x150:344 possible LOD records','root+0x180:75 secondary records; associations not yet admitted'],
        'limitations':['Typed FAB mask, assembly field, pose and descriptor interpretations are corroborated by stored bounds, not native renderer semantics.',
            'Only first12-byte positions and verified full triangle buffers used; no skinning, normals, UV or material interpretation.',
            'Invented per-model colors and computed face normals; no original lighting or texture claim.',
            'No collision, gameplay, dynamic entities, or complete scene claim.']}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('space',type=Path)
    ap.add_argument('--mesh-root',type=Path,required=True);ap.add_argument('--fab-root',type=Path,required=True)
    ap.add_argument('--native-root',type=Path,required=True);ap.add_argument('--scene-bin',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--allow-partial',action='store_true');args=ap.parse_args()
    report=bake(args.space.read_bytes(),args.mesh_root,args.fab_root,args.native_root,args.scene_bin,args.allow_partial)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in {'model_inputs','admitted_records','omitted_records','native_carrier_evidence'}},indent=2))

if __name__=='__main__':main()
