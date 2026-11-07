from pathlib import Path
import subprocess,shlex,json,statistics,sys
root=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-benchmark');out=root/'evidence';out.mkdir(exist_ok=True)
adb=['/opt/homebrew/bin/adb','-s','99cc517a']
def pull(remote,local):
 with local.open('wb') as f:subprocess.run(adb+['exec-out','su -c '+shlex.quote('cat '+remote)],stdout=f,check=True)
results={}
for name in sys.argv[1:]:
 d=out/name;d.mkdir(exist_ok=True)
 base='/data/user/0/org.openamalur.nativebenchmark/files/'+name
 for fn in ['measurements.json','replay.log']:pull(base+'/'+fn,d/fn)
 j=json.loads((d/'measurements.json').read_text())['frame_range'];v=j['frame_durations'];print(name,len(v),j['fps'])
 results[name]={'fps':j['fps'],'measured_frames':j['frame_count'],'seconds':j['duration'],'process_cpu_seconds':j['end_time_process']-j['start_time_process'],'mean_ms':statistics.mean(v)/1e6,'median_ms':statistics.median(v)/1e6,'p95_ms':sorted(v)[int(.95*(len(v)-1))]/1e6}
(out/'latest-summary.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
