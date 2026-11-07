import sys;sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
import configparser,time,subprocess,json,re
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');Q=P/'work/v46-canopy';D=Q/'reference-data';prop=D/'properties.ini';log=D/'desktop.log'
def setp(**kw):
 c=configparser.ConfigParser();c.read(prop,encoding='utf-8')
 for k,v in kw.items():c['properties']['debug.opem.'+k]=str(v)
 with prop.with_suffix('.tmp').open('w',encoding='utf-8') as f:c.write(f)
 prop.with_suffix('.tmp').replace(prop)
def waitfor(needle,start):
 end=time.monotonic()+12
 while time.monotonic()<end:
  data=log.read_text(encoding='utf-8',errors='replace')[start:]
  if needle in data:return data
  time.sleep(.05)
 raise RuntimeError(needle)
results=[]
for mode in [-1,0]:
 tag='dense' if mode<0 else 'corrected';start=len(log.read_text(encoding='utf-8',errors='replace'));setp(canopy=mode,materialprobe=-1);waitfor('stage=final',start)
 start=len(log.read_text(encoding='utf-8',errors='replace'));setp(materialprobe=0);data=waitfor('DepthProbe error=',start);lines=[l for l in data.splitlines() if 'DepthProbe' in l or 'stage=final' in l];(Q/('windows-'+tag+'-probes.log')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
 r=subprocess.run([sys.executable,str(P/'work/v40-windows-host/control.py'),'capture','--user-data',str(D),'--out',str(Q/('windows-'+tag+'-stable.png'))],capture_output=True,text=True);assert not r.returncode,r.stderr
 match=re.search(r'DepthProbe pixel=980,100 raw24=(\d+)',data);assert match;depth=int(match[1]);expected=16762614 if mode<0 else 16777215;assert depth==expected,(tag,depth,expected);results.append(dict(mode=tag,depth_980_100=depth,expected=expected,passed=True))
(Q/'windows-depth-ab.json').write_text(json.dumps(results,indent=2),encoding='utf-8');print(json.dumps(results,indent=2))
