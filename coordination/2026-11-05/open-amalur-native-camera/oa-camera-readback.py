from pathlib import Path
import argparse,subprocess,shlex,struct,json
p=argparse.ArgumentParser();p.add_argument('run');a=p.parse_args();r=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera/evidence')/a.run;r.mkdir(parents=True,exist_ok=True)
adb=['/opt/homebrew/bin/adb','-s','99cc517a'];base='/data/user/0/org.openamalur.nativebenchmark/files/'+a.run
for name in ['replay.log','screenshot_frame_1.bmp','screenshot_frame_30.bmp']:
 with (r/name).open('wb') as f:subprocess.run(adb+['exec-out','su -c '+shlex.quote('cat '+base+'/'+name)],check=True,stdout=f)
def read(p):
 b=Path(p).read_bytes();off=struct.unpack_from('<I',b,10)[0];w,h=struct.unpack_from('<ii',b,18);n=struct.unpack_from('<H',b,28)[0]//8;stride=(w*n+3)//4*4;rows=[b[off+i*stride:off+i*stride+w*n] for i in range(abs(h))]
 if h>0:rows.reverse()
 return (w,abs(h)),bytes(v for row in rows for i in range(w) for v in row[i*n:i*n+3])
base=read('/private/tmp/oa-android-loop-first.bmp');first=read(r/'screenshot_frame_1.bmp');last=read(r/'screenshot_frame_30.bmp');result={'dimensions':last[0],'first_equals_last':first==last,'first_equals_raw':first==base,'last_equals_raw':last==base,'changed_channels_vs_raw':sum(x!=y for x,y in zip(last[1],base[1]))};(r/'image-check.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
print('\n'.join(x for x in (r/'replay.log').read_text().splitlines() if 'OA CAMERA' in x))
subprocess.run(['/usr/bin/sips','-s','format','png',str(r/'screenshot_frame_30.bmp'),'--out',str(r/'last.png')],check=True,stdout=subprocess.DEVNULL)
