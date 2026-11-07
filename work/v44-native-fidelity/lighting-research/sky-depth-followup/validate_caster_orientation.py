from pathlib import Path
import json,struct,numpy as np
p=Path(__file__).parent;root=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera');pipes=json.loads((root/'pipeline-index.json').read_text());phases=json.loads((p.parent/'phases.json').read_text());r=[]
for phase in [99,101,103]:
 ph=next(x for x in phases if x['phase']==phase);counts={}
 for d in ph['draws']:counts[d['pipeline']]=counts.get(d['pipeline'],0)+1
 r.append({'phase':phase,'pipelines':[{'pipeline':i,'draws':n,'frontFace':pipes[str(i)]['pRasterizationState']['frontFace'],'cullMode':pipes[str(i)]['pRasterizationState']['cullMode']} for i,n in counts.items()]})
d=json.loads((p/'first-caster.json').read_text());u=d['uniforms'][0]['values'];M=np.asarray(u[32:48]).reshape(4,4).T;W=np.asarray(u[:16]).reshape(4,4).T;C=M@np.linalg.inv(W)
# GL changes Z only; these unchanged XY NDC areas directly identify GL winding.
P=np.asarray([[0,0,0,1],[100,0,0,1],[0,100,0,1]]);q=P@C.T;q=q[:,:2]/q[:,3,None];area=float(np.linalg.det(np.asarray([q[1]-q[0],q[2]-q[0]])))
v=np.asarray(list(struct.iter_unpack('<12f',(p/'buffer-12236.bin').read_bytes())))[:,:3];v=np.c_[v,np.ones(len(v))];ix=np.asarray(struct.unpack('<2844H',(p/'buffer-12238.bin').read_bytes())).reshape(-1,3);clip=v@M.T;ndc=clip[:,:2]/clip[:,3,None];areas=[]
for ids in ix:
 a,b,c=ndc[ids];areas.append(float(np.linalg.det(np.asarray([b-a,c-a]))))
report={'phases':r,'nativeViewport':{'x':0,'y':1024,'width':1024,'height':-1024},'GL_adapter':'Z only: zGL=2*zD3D-w; XY unchanged','captured_far_VP_world_XY_CCW_triangle_NDC_area':area,'world_XY_triangle_GL_frontface':'CW','first_actual_caster':{'draw':69945,'triangles':len(areas),'NDC_CW':sum(a<0 for a in areas),'NDC_CCW':sum(a>0 for a in areas),'degenerate':sum(a==0 for a in areas),'first_12_NDC_areas':areas[:12]},'gpu_execution':False}
(p/'caster-orientation-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='phases'},indent=2))
