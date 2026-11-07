from pathlib import Path
import json,re,subprocess,sys,time
adb='/opt/homebrew/bin/adb';scale=int(sys.argv[1]);assert scale in [100,75,50]
out=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-windows-host/v44-native-fidelity/android-validation/scaling');out.mkdir(exist_ok=True);prefix=out/f'scale-{scale}';assert not prefix.with_suffix('.json').exists()
def run(*args):return subprocess.check_output([adb,*args],text=True)
run('shell','setprop','debug.opem.scale',str(scale));thermal_before=run('shell','dumpsys','thermalservice');start=time.monotonic();
if '--attach' not in sys.argv:print(run('shell','am','start','-n','org.opemamalur.scene/android.app.NativeActivity'),flush=True)
pid='';text='';profiles=[];deadline=start+52
while time.monotonic()<deadline:
 pid=subprocess.run([adb,'shell','pidof','org.opemamalur.scene'],capture_output=True,text=True).stdout.strip()
 if pid:
  text=run('logcat','-d','--pid='+pid,'-v','brief','-s','OpemAmalurScene:I')
  profiles=re.findall(r'PROFILE interval_ms=([^\n]+)',text)
  # Three complete steady windows after initialization; preserve full log.
  if len(profiles)>=4 and 'queued=0' in text:break
 time.sleep(2)
assert pid and len(profiles)>=2,(pid,len(profiles),text[-2500:]);prefix.with_suffix('.log').write_text(text)
def fields(s):return {k:float(v) if re.match(r'^-?[\d.]+$',v) else v for k,v in re.findall(r'(\w+)=([^ ]+)',s)}
records=[fields('interval_ms='+x) for x in profiles];steady=records[-3:] if len(records)>3 else records[1:]
result={'requested_scale':scale,'pid':pid,'elapsed_seconds':time.monotonic()-start,'profiles':records,'steady_windows':steady,'mean_fps':sum(1000/x['interval_ms'] for x in steady)/len(steady),'mean_gpu_ms':sum(x['gpu_ms'] for x in steady)/len(steady),'mean_submit_ms':sum(x['submit_ms'] for x in steady)/len(steady),'scale_logs':[x for x in text.splitlines() if 'Render scale requested=' in x],'native_features_ran':[x for x in text.splitlines() if 'Native fidelity rendered' in x or 'Native DOF rendered=' in x],'latest_stream':next((x for x in reversed(text.splitlines()) if 'STREAM cells=' in x),None),'thermal_before':re.search(r'Thermal Status: (\d+)',thermal_before).group(1),'thermal_after':re.search(r'Thermal Status: (\d+)',run('shell','dumpsys','thermalservice')).group(1),'scope':'Short stationary v0.35 R4 scene sample, vsync enabled; repeated same pose, live wind/actors, not a sustained benchmark'}
assert result['native_features_ran'];actual=[x['size'] for x in steady];expected=f'{2520*scale//100}x{1680*scale//100}';assert all(x==expected for x in actual),(actual,expected,result['scale_logs'])
prefix.with_suffix('.json').write_text(json.dumps(result,indent=2));prefix.with_suffix('.png').write_bytes(subprocess.check_output([adb,'exec-out','screencap','-p']));print(json.dumps({k:v for k,v in result.items() if k not in ['profiles','thermal_before','thermal_after']},indent=2))
