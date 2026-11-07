from pathlib import Path
import subprocess,json,platform
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';out=r/'outputs/scene-v08';b=r/'work/v08-portable/build-windows';runtime=r/'work/v08-portable/runtime'
tests=[('controller-state',119),('android-layout',97),('content-state',460),('platform-state',24),('fresh-profile',105),('quick-save-state',24),('player-registry',3042),('enum-snapshot',64),('language-catalog',52),('renderer-cap',34),('bootstrap-order',37),('empty-object-handle',22)]
results=[]
for name,count in tests:
 p=subprocess.run([str(b/f'amalur-{name}-test.exe'),str(runtime)],capture_output=True,timeout=120)
 text=p.stdout.decode(errors='replace');(out/(name+'-tests.txt')).write_text(text+p.stderr.decode(errors='replace'));j=json.loads(text)
 ok=p.returncode==0 and j.get('ok') and (count is None or j.get('checks')==count)
 results.append({'test':name,'ok':bool(ok),'exit_code':p.returncode,'result':j});print(name,ok,j.get('checks'))
for name,args in [('asset-macro',[str(runtime),str(out/'assets/loottable_init.bin')]),('lua-weak-mode',[str(r/'work/v08-portable/tests/lua_weak_mode_test.lua')])]:
 p=subprocess.run([str(b/f'amalur-{name}-test.exe'),*args],capture_output=True,timeout=120);text=p.stdout.decode(errors='replace');(out/(name+'-tests.txt')).write_text(text+p.stderr.decode(errors='replace'));results.append({'test':name,'ok':p.returncode==0,'exit_code':p.returncode,'stdout':text});print(name,p.returncode,text[:160])
j={'ok':all(x['ok'] for x in results),'platform':'Windows x64','scope':'Current portable services and captured-value/table-key support; no native whole-game behavior parity','tests':results};(out/'windows-services-validation.json').write_text(json.dumps(j,indent=2));raise SystemExit(0 if j['ok'] else 1)
