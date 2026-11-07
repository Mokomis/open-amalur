"""File-only control of this Windows development host; no global keyboard injection."""
from pathlib import Path
import argparse,time,shutil
w=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('action',choices=['capture','tap','key','close','status']);p.add_argument('value',nargs='?');p.add_argument('--ms',type=int,default=100);p.add_argument('--down',type=int,choices=[0,1],default=1);p.add_argument('--out',type=Path);p.add_argument('--user-data',type=Path,default=w/'user-data');a=p.parse_args()
log=a.user_data/'desktop.log';queue=a.user_data/'control.txt'
if a.action=='status':
 print(log.read_text(errors='replace')[-4000:] if log.exists() else 'Host has not started');raise SystemExit()
key=ord(a.value.upper()) if a.value and len(a.value)==1 else int(a.value or '0')
if a.action=='tap':command=f'tap {key} {max(20,min(5000,a.ms))}\n'
elif a.action=='key':command=f'key {key} {a.down}\n'
else:command=a.action+'\n'
if queue.exists():raise SystemExit('A control request is pending; preserve it')
before=log.stat().st_size if log.exists() else 0
tmp=queue.with_suffix('.tmp');tmp.write_text(command,encoding='ascii');tmp.replace(queue)
deadline=time.monotonic()+20
while queue.exists() and time.monotonic()<deadline:time.sleep(.05)
if queue.exists():raise SystemExit('Host did not consume the request; no retry issued')
if a.action=='capture':
 while time.monotonic()<deadline:
  with log.open('r',errors='replace') as f:f.seek(before);new=f.read()
  if 'Captured frame=' in new:break
  time.sleep(.05)
 else:raise SystemExit('No successful capture recorded')
 source=Path([line for line in new.splitlines() if 'Captured frame=' in line][-1].split(' path=',1)[1])
 if a.out:
  a.out.parent.mkdir(parents=True,exist_ok=True)
  if a.out.exists():raise SystemExit('Refusing to overwrite an evidence capture')
  if a.out.suffix.lower()=='.png':
   from PIL import Image
   with Image.open(source) as im:im.save(a.out)
  else:shutil.copy2(source,a.out)
 meta=source.with_name(source.name+'.json')
 if a.out and meta.exists():shutil.copy2(meta,a.out.with_suffix('.json'))
 print(new.strip(),a.out or source)
else:print('Consumed:',command.strip())
