"""Launch the custom Windows engine, with its own assets and user data."""
from pathlib import Path
import argparse,subprocess,sys,csv,ctypes
w=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--scene',choices=['town','title','reference'],default='town');p.add_argument('--frames',type=int,default=0);p.add_argument('--user-data',type=Path);a=p.parse_args()
exe=w/'build/open-amalur-windows.exe'
if not exe.exists():raise SystemExit('Build the Windows host first: build.cmd')
rows=csv.reader(subprocess.check_output(['tasklist','/FI','IMAGENAME eq open-amalur-windows.exe','/FO','CSV','/NH'],text=True).splitlines())
if any(row and row[0].lower()=='open-amalur-windows.exe' for row in rows):raise SystemExit('A preview is running. Close it with control.py before starting another.')
userdata=a.user_data or w/('reference-data' if a.scene=='reference' else 'user-data');userdata.mkdir(exist_ok=True)
if a.scene=='reference' and not (userdata/'native-camera.txt').exists():raise SystemExit('Reference camera evidence has not been prepared.')
captures=w/'captures';captures.mkdir(exist_ok=True)
args=[str(exe),'--assets',str(w/'assets'),'--user-data',str(userdata),'--capture',str(captures/(a.scene+'-latest.bmp')),'--capture-frame','1200']
if a.scene!='title':args.append('--town')
if a.frames>0:args+=['--frames',str(a.frames)]
p=subprocess.Popen(args,cwd=w,creationflags=subprocess.CREATE_NO_WINDOW)
(w/'host.pid').write_text(str(p.pid)+'\n')
(w/'active-user-data.txt').write_text(str(userdata)+'\n')
print('PID',p.pid,'scene',a.scene,'user data',userdata)
