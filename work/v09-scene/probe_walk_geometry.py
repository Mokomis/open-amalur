from pathlib import Path
import struct,json,math,platform,sys
from collections import defaultdict
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';b=(r/'outputs/scene-v07/scene.bin').read_bytes();assert b[:8]==b'OMSC07\0\0';count=struct.unpack_from('<I',b,8)[0];assert len(b)==36+count*36
bins=defaultdict(lambda:{'area':0.,'triangles':0,'centers':[]})
for i in range(0,count,3):
 pts=[struct.unpack_from('<3f',b,36+(i+k)*36) for k in range(3)];u=[pts[1][a]-pts[0][a] for a in range(3)];v=[pts[2][a]-pts[0][a] for a in range(3)];n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];length=math.sqrt(sum(x*x for x in n))
 if length>1e-4 and abs(n[2])/length>.98:
  center=[sum(p[a] for p in pts)/3 for a in range(3)];bucket=round(center[2]/5)*5;d=bins[bucket];d['area']+=length/2;d['triangles']+=1
  if length>20000:d['centers'].append({'center':center,'area':length/2,'up':n[2]>0})
summary=[{'z_bucket':z,**d} for z,d in sorted(bins.items(),key=lambda x:-x[1]['area'])[:15]]
shell=json.load(open(r/'outputs/scene-v07/shell-candidate.json'));floor=[x for x in shell['admitted_records'] if x['material_id_candidate']==493000]
result={'scope':'Observed world render geometry, horizontal-face distribution; not recovered physics','horizontal_layers':summary,'hardwood_material_records':floor};(r/'outputs/scene-v09/walk-geometry-probe.json').write_text(json.dumps(result,indent=2));print(json.dumps({'layers':[{k:v for k,v in x.items() if k!='centers'} for x in summary],'hardwood_records':[{'position':x['position_xyz'],'sphere':x['sphere'],'fab':x['fab_id'],'assembly':x['assembly']} for x in floor]},indent=2))
