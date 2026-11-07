import sys,platform,subprocess,json,hashlib
from pathlib import Path
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';o=r/'outputs/scene-v09';b=r/'work/v09-host/build-windows';results=[]
for name,args in [('input',[b/'amalur-exploration-input-test.exe']),('collision',[b/'amalur-collision-test.exe']),('materials',[b/'amalur-material-test.exe']),('walk',[b/'amalur-walk-scene.exe',r/'outputs/scene-v07/scene.bin']),('texture-decoder',[sys.executable,'-m','unittest','discover','-s',r/'work/v09-textures','-p','test_keen_texture.py','-v'])]:
 p=subprocess.run([str(a) for a in args],cwd=r,capture_output=True,timeout=60);(o/f'final-{name}.log').write_bytes(p.stdout+p.stderr)
 results.append(dict(name=name,exit_code=p.returncode,log=f'final-{name}.log'))
 if p.returncode:raise RuntimeError(name+' failed')
 if name=='walk':(o/'walk-scene-final.json').write_bytes(p.stdout)
v=dict(windows_checks_passed=True,checks=results,device_executed=False,device_blocker='Tablet absent from Mac and Windows adb inventories on 2026-10-30.',texture_preview=json.loads((o/'materials-expanded.json').read_text()),limitations=['Authored approximate capsule collision against recovered render triangles; native collision data unimplemented.','Grounded walking stops at missing floors/drop-offs; no jumping.','Slot-zero opaque textures and stride48 UVs are explicit preview assumptions, not original shader equivalence.','Props and unsupported material/layout ranges retain diagnostic colors.','Tablet input, rendering, performance and lifecycle remain unverified for v0.9.'])
(o/'scene-validation.json').write_text(json.dumps(v,indent=2));print(json.dumps(dict(windows_checks_passed=True,tests=results),indent=2))
