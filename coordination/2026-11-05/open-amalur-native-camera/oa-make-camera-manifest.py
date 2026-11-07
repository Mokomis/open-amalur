from pathlib import Path
import json,math,struct,collections
r=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera');j=json.loads((r/'capture-index.json').read_text());mem={n:(r/f'memory-{n}.bin').read_bytes() for n in [52,60,7801]};selected={};coverage=collections.Counter();rejected=collections.Counter()
for d in j['draws']:
 if d['index']<62468:continue
 matched=False
 for u in d['uniforms']:
  if u['binding']!=68 or u['range']<192 or u['memory'] not in mem:continue
  m=struct.unpack_from('<16f',mem[u['memory']],u['offset']+128)
  # Perspective camera WVP has z_i=q*w_i for affine input basis rows0..2;
  # orthographic shadow/UI matrices instead have all three w_i=0.
  q=1.00005;norm=sum(m[i*4+3]**2 for i in range(3))
  ok=norm>1e-8 and all(abs(m[i*4+2]-q*m[i*4+3])<max(1e-4,abs(m[i*4+3])*2e-5) for i in range(3))
  if not ok:rejected[d['phase']]+=1;continue
  key=(u['memory'],u['offset']+128);selected[key]={'memory':key[0],'offset':key[1],'base':m,'phases':set()};matched=True
  selected[key]['phases'].add(d['phase'])
 if matched:coverage[d['phase']]+=1
out={'projection':{'fx':1.311111211,'fy':2.33086443,'q':1.00005,'near_term':-26.1875},'matrix_count':len(selected),'covered_draws_by_phase':dict(coverage),'rejected_by_phase':dict(rejected),'matrices':[dict(v,phases=sorted(v['phases'])) for v in selected.values()]}
# Exact projection scales from camera basis norms, independent of its rotation.
m=out['matrices'][0]['base'];out['projection']['fx']=math.sqrt(sum(m[i*4]**2 for i in range(3)));out['projection']['fy']=math.sqrt(sum(m[i*4+1]**2 for i in range(3)));qs=[m[i*4+2]/m[i*4+3] for i in range(3) if abs(m[i*4+3])>.1];out['projection']['q']=sum(qs)/len(qs)
(r/'camera-manifest.json').write_text(json.dumps(out,indent=2)+'\n')
print({k:v for k,v in out.items() if k!='matrices'})
