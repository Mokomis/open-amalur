"""Test scaled-origin versus scaled-center diagnostic hypotheses, without baking."""
from pathlib import Path
from collections import Counter
import argparse,json,platform
from amalur_shell import selected_records,load_model,distance,render_pose
assert platform.system()=='Windows'
ap=argparse.ArgumentParser();ap.add_argument('space',type=Path);ap.add_argument('--mesh-root',type=Path,required=True)
ap.add_argument('--fab-root',type=Path,required=True);ap.add_argument('--native-root',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
args=ap.parse_args();records,_=selected_records(args.space.read_bytes());models={}
for key in {r['fab_id'] for r in records}:
    model,error=load_model(key,args.mesh_root,args.fab_root,args.native_root)
    if model:models[key]=model
rows=[];centers=Counter();enclosures=Counter()
for record in records:
    if record['fab_id'] not in models:continue
    model=models[record['fab_id']];mesh=model['mesh'];desc=model['fab']['mesh_descriptors'][record['assembly']]
    assembly=mesh['assemblies'][record['assembly']];positions=mesh['vertex_buffers'][assembly['vertex_buffer']]['positions']
    center=desc['position_xyz_uninterpreted'];unit=dict(record,scale_xyz=[1.,1.,1.]);tests=[]
    for mode in ['origin_scaling','no_vertex_scaling','descriptor_center_scaling']:
        def apply(p):
            if mode=='origin_scaling':return render_pose(p,record)
            if mode=='no_vertex_scaling':return render_pose(p,unit)
            centered=[center[i]+(p[i]-center[i])*record['scale_xyz'][i] for i in range(3)]
            return render_pose(centered,unit)
        center_error=distance(apply(center),record['sphere'][:3])
        values=[distance(apply(p),record['sphere'][:3]) for p in positions]
        outside=sum(d>record['sphere'][3]+.1 for d in values)
        tests.append({'mode':mode,'center_error':center_error,'vertices_outside':outside,'maximum_vertex_distance':max(values)})
        if center_error<=.01:
            centers[mode]+=1
            if outside==0:enclosures[mode]+=1
    rows.append({'reference_index':record['reference_index'],'fab_id':record['fab_id'],'assembly':record['assembly'],
        'scale':record['scale_xyz'],'descriptor_center':center,'sphere_radius':record['sphere'][3],'tests':tests})
report={'scope':'Geometry hypotheses measured against stored spheres only; no native scale-origin proof and no scene write',
        'summary':{'tested_records':len(rows),'center_pass_counts':dict(centers),'center_and_enclosure_pass_counts':dict(enclosures)},'records':rows}
args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2,allow_nan=False),encoding='utf-8')
print(json.dumps(report['summary'],indent=2))
