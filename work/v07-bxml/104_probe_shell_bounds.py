"""Windows-only test of candidate assembly and transform associations.

Produces measurements only. Neither the static-bind nor precomposed hypothesis
is admitted for rendering by this script, including unknown vertex layouts.
"""
import argparse,json,math,platform
from pathlib import Path
assert platform.system()=='Windows'
ap=argparse.ArgumentParser();ap.add_argument('--mesh',type=Path,required=True);ap.add_argument('--fab',type=Path,required=True)
ap.add_argument('--mapping',type=Path,required=True);ap.add_argument('--asset-id',type=int,required=True);ap.add_argument('--output',type=Path,required=True)
args=ap.parse_args();mesh=json.loads(args.mesh.read_text());fab=json.loads(args.fab.read_text());mapping=json.loads(args.mapping.read_text())
def point(matrix,p):return tuple(sum(matrix[r*4+i]*p[i] for i in range(3))+matrix[r*4+3] for r in range(3))
def pose(record,p):
    x,y,z=[p[i]*record['scale'][i] for i in range(3)];qx,qy,qz,qw=record['quaternion']
    tx=2*(qy*z-qz*y);ty=2*(qz*x-qx*z);tz=2*(qx*y-qy*x)
    v=(x+qw*tx+qy*tz-qz*ty,y+qw*ty+qz*tx-qx*tz,z+qw*tz+qx*ty-qy*tx)
    return tuple(v[i]+record['position'][i] for i in range(3))
def distance(a,b):return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))
rows=[]
for group in mapping['groups']:
    for reference in group['rows']:
        if reference['fab_id_candidate']!=args.asset_id:continue
        for key in ['sphere_match_record','pose_match_record']:
            if key not in reference:continue
            record=reference[key];center=record['sphere'][:3];radius=record['sphere'][3]
            tests=[]
            for i,(assembly,descriptor) in enumerate(zip(mesh['assemblies'],fab['mesh_descriptors'])):
                positions=mesh['vertex_buffers'][assembly['vertex_buffer']]['positions']
                for mode in ['scene_pose_only','fab_bind_then_scene_pose']:
                    matrix=descriptor.get('static_bind_candidate') if mode=='fab_bind_then_scene_pose' else None
                    if mode=='fab_bind_then_scene_pose' and matrix is None:continue
                    local_center=descriptor['position_xyz_uninterpreted']
                    if matrix:local_center=point(matrix,local_center)
                    predicted_center=pose(record,local_center)
                    distances=[distance(pose(record,point(matrix,p) if matrix else p),center) for p in positions]
                    tests.append({'assembly':i,'mode':mode,'descriptor_center_error':distance(predicted_center,center),
                        'descriptor_predicted_center':predicted_center,'vertices':len(positions),
                        'vertices_outside_sphere_tolerance_0_1':sum(d>radius+.1 for d in distances),
                        'maximum_vertex_distance':max(distances),'radius':radius,
                        'descriptor_radius_candidate':descriptor['unknown_four_floats'][1],
                        'vertex_stride':mesh['vertex_buffers'][assembly['vertex_buffer']]['stride_bytes']})
            tests.sort(key=lambda t:t['descriptor_center_error'])
            rows.append({'render_slot':group['render_slot'],'reference_index':reference['reference_index'],
                'match_basis':key,'render_index':record['render_index'],'tests':tests})
result={'source_mesh_json':str(args.mesh),'source_fab_json':str(args.fab),'source_mapping_json':str(args.mapping),
        'asset_id':args.asset_id,'scope':'Diagnostic geometry measurements, no native semantic confirmation or render admission',
        'records':rows}
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
print(json.dumps({'output':str(args.output),'records':len(rows),'best':[{'reference_index':r['reference_index'],'match_basis':r['match_basis'],'render_index':r['render_index'],'best':r['tests'][0]} for r in rows]},indent=2))
