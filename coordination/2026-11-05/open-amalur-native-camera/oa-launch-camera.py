import argparse,json,shlex,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--name',default='camera-live');p.add_argument('--loops',type=int);p.add_argument('--screenshots',default='');p.add_argument('--offscreen',action='store_true');p.add_argument('--yaw',type=float,default=0);p.add_argument('--pitch',type=float,default=0);p.add_argument('--right',type=float,default=0);p.add_argument('--forward',type=float,default=0);a=p.parse_args();assert a.name.replace('-','').replace('_','').isalnum()
adb=['/opt/homebrew/bin/adb','-s','99cc517a'];pkg='org.openamalur.nativebenchmark';base='/data/user/0/'+pkg+'/files';out=base+'/'+a.name

def shell(c):return subprocess.run(adb+['shell',c],capture_output=True,text=True,check=True).stdout
def root(c):return shell('su -c '+shlex.quote(c))
root('mkdir -p '+out+' && chown 10308:10308 '+out+' && restorecon -R '+out)
pose=f'{a.yaw} {a.pitch} {a.right} {a.forward}\n'
root('printf %s '+shlex.quote(pose)+' > '+base+'/camera.txt && chown 10308:10308 '+base+'/camera.txt && restorecon '+base+'/camera.txt')
args=['--loop-frame','1','--remove-unsupported','--memory-translation','rebind','--opcd','--log-file',out+'/replay.log']
if a.loops:args+=['--loop-count',str(a.loops)]
if a.offscreen:args+=['--swapchain','offscreen']
if a.screenshots:args+=['--screenshots',a.screenshots,'--screenshot-dir',out]
args+=[base+'/dalentarth.gfxr']
shell('input keyevent KEYCODE_WAKEUP');shell('wm dismiss-keyguard');shell('am force-stop '+pkg)
print(shell(shlex.join(['am','start','-n',pkg+'/android.app.NativeActivity','--es','args',shlex.join(args),'--es','oa_static_memory','2','--es','oa_camera','1'])))
print(json.dumps({'results':out,'pose':pose,'loops':a.loops}),flush=True)
if a.loops:
 start=time.monotonic()
 while time.monotonic()-start<55:
  time.sleep(1)
  if not shell('pidof '+pkg+' || true').strip():break
 else:raise RuntimeError('Benchmark still running; not stopping without inspecting its log')
 print(root('tail -6 '+out+'/replay.log'))
