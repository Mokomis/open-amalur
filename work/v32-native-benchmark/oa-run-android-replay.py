import argparse,json,shlex,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--loops',type=int,default=3);p.add_argument('--warmup',type=int,default=1);p.add_argument('--screenshots',default='');p.add_argument('--visible',action='store_true');p.add_argument('--profile',action='store_true');p.add_argument('--static-memory',action='store_true');p.add_argument('--static-resources',action='store_true');a=p.parse_args()
assert a.name.replace('-','').replace('_','').isalnum() and 1<=a.warmup<a.loops<=20000
adb=['/opt/homebrew/bin/adb','-s','99cc517a'];pkg='org.openamalur.nativebenchmark';base='/data/user/0/'+pkg+'/files';out=base+'/'+a.name

def shell(cmd):return subprocess.run(adb+['shell',cmd],check=True,capture_output=True,text=True).stdout
def root(cmd):return shell('su -c '+shlex.quote(cmd))
root('mkdir -p '+shlex.quote(out)+' && chown 10308:10308 '+shlex.quote(out)+' && restorecon -R '+shlex.quote(out))
options=['--loop-frame','1','--loop-count',str(a.loops),'--remove-unsupported','--memory-translation','rebind','--opcd','--measurement-frame-range',str(a.warmup+1)+'-'+str(a.loops+1),'--measurement-file',out+'/measurements.json','--flush-measurement-range','--log-file',out+'/replay.log']
if not a.visible:options+=['--swapchain','offscreen']
if a.screenshots:options+=['--screenshots',a.screenshots,'--screenshot-dir',out]
options+=[base+'/dalentarth.gfxr']
# Only this separate test app is stopped; no existing game/app is touched.
shell('input keyevent KEYCODE_WAKEUP')
shell('wm dismiss-keyguard')
shell('am force-stop '+pkg)
launch=['am','start','-n',pkg+'/android.app.NativeActivity','--es','args',shlex.join(options)]
if a.static_resources:launch+=['--es','oa_static_memory','2']
elif a.static_memory:launch+=['--es','oa_static_memory','1']
result=shell(shlex.join(launch))
print(json.dumps({'activity_start':result,'private_results':out,'args':options}),flush=True)
start=time.monotonic()
if a.profile:
 time.sleep(4)
 perf='/data/local/tmp/oa-native-'+a.name+'.data'
 cmd='BENCH_PID=$(pidof '+pkg+'); test -n "$BENCH_PID" && simpleperf record -p "$BENCH_PID" -e cpu-cycles -f 99 --duration 8 -o '+shlex.quote(perf)+' && simpleperf report -i '+shlex.quote(perf)+' --sort dso,symbol --percent-limit 1 | head -75'
 print(root(cmd),flush=True)

while time.monotonic()-start<55:
 time.sleep(1)
 pid=shell('pidof '+pkg+' || true').strip()
 if not pid:break
else:
 print('TIMEOUT; stopping owned benchmark app',flush=True);shell('am force-stop '+pkg)
print(root('ls -l '+shlex.quote(out)+'; tail -45 '+shlex.quote(out+'/replay.log')+'; cat '+shlex.quote(out+'/measurements.json')+' 2>/dev/null || true'),flush=True)
