"""Read-only competing-transform measurements; no admission thresholds change."""
from pathlib import Path
from collections import Counter
import argparse,json,math,platform
from amalur_shell import selected_records,load_model,distance
assert platform.system()=='Windows'
ap=argparse.ArgumentParser();ap.add_argument('space',type=Path);ap.add_argument('--mesh-root',type=Path,required=True)
ap.add_argument('--fab-root',type=Path,required=True);ap.add_argument('--native-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
args=ap.parse_args();records,_=selected_records(args.space.read_bytes());models={}
for key in {r['fab_id'] for r in records}:
    model,error=load_model(key,args.mesh_root,args.fab_root,args.native_root)
    if model:models[key]=model
def matpoint(m,p):return tuple(sum(m[r*4+i]*p[i] for i in range(3))+m[r*4+3] for r in range(3))
def inverse(m):
    a,b,c,d,e,f,g,h,i=[m[k] for k in [0,1,2,4,5,6,8,9,10]]
    det=a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g)
    if abs(det)<1e-12:return None
    q=[(e*i-f*h)/det,(c*h-b*i)/det,(b*f-c*e)/det,0,
       (f*g-d*i)/det,(a*i-c*g)/det,(c*d-a*f)/det,0,
       (d*h-e*g)/det,(b*g-a*h)/det,(a*e-b*d)/det,0,0,0,0,1]
    for r in range(3):q[r*4+3]=-sum(q[r*4+j]*m[j*4+3] for j in range(3))
    return q
def apply(record,p,conjugate,scale_first,matrix):
    if matrix:p=matpoint(matrix,p)
    x,y,z=[p[j]*(record['scale_xyz'][j] if scale_first else 1) for j in range(3)]
    qx,qy,qz,qw=record['quaternion_xyzw']
    if conjugate:qx,qy,qz=-qx,-qy,-qz
    tx=2*(qy*z-qz*y);ty=2*(qz*x-qx*z);tz=2*(qx*y-qy*x)
    rotated=(x+qw*tx+qy*tz-qz*ty,y+qw*ty+qz*tx-qx*tz,z+qw*tz+qx*ty-qy*tx)
    return tuple(rotated[j]*(1 if scale_first else record['scale_xyz'][j])+record['position_xyz'][j] for j in range(3))
rows=[];counts=Counter();enclosed=Counter()
for record in records:
    if record['fab_id'] not in models:continue
    model=models[record['fab_id']];mesh=model['mesh'];desc=model['fab']['mesh_descriptors'][record['assembly']]
    assembly=mesh['assemblies'][record['assembly']];positions=mesh['vertex_buffers'][assembly['vertex_buffer']]['positions']
    matrix=desc.get('static_bind_candidate');matrices={'none':None}
    if matrix:
        matrices['bind']=matrix;inv=inverse(matrix)
        if inv:matrices['inverse_bind']=inv
    tests=[]
    radius=desc['unknown_four_floats'][1]*max(map(abs,record['scale_xyz']))
    radius_error=abs(radius-record['sphere'][3])
    for bind,m in matrices.items():
        for conjugate in [False,True]:
            for first in [True,False]:
                label=f'{bind}:q{"conjugate" if conjugate else "direct"}:scale{"before" if first else "after"}'
                center=apply(record,desc['position_xyz_uninterpreted'],conjugate,first,m)
                error=distance(center,record['sphere'][:3]);test={'variant':label,'center_error':error}
                if error<=.01:
                    counts[label]+=1
                    distances=[distance(apply(record,p,conjugate,first,m),record['sphere'][:3]) for p in positions]
                    outside=sum(d>record['sphere'][3]+.1 for d in distances)
                    test.update(vertices_outside=outside,maximum_vertex_distance=max(distances))
                    if not outside:enclosed[label]+=1
                tests.append(test)
    tests.sort(key=lambda t:t['center_error'])
    rows.append({'reference_index':record['reference_index'],'render_index':record['render_index'],'fab_id':record['fab_id'],
        'assembly':record['assembly'],'quaternion':record['quaternion_xyzw'],'scale':record['scale_xyz'],
        'sphere_radius':record['sphere'][3],'predicted_radius':radius,'radius_error':radius_error,
        'radius_pass':radius_error<=max(.01,record['sphere'][3]*1e-5),'tests':tests})
report={'scope':'Competing arithmetic hypotheses only; original scene/candidate unchanged','records':rows,
        'summary':{'tested_records':len(rows),'radius_passes':sum(r['radius_pass'] for r in rows),
                   'center_pass_counts':dict(counts),'center_and_enclosure_pass_counts':dict(enclosed)}}
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
print(json.dumps(report['summary'],indent=2))
