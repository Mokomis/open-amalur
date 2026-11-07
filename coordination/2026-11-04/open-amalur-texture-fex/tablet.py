"""Small explicit-device ADB helper; root commands are safely quoted as one string."""
import argparse,shlex,subprocess,sys,time
from pathlib import Path
SERIAL='99cc517a'
p=argparse.ArgumentParser();sub=p.add_subparsers(dest='action',required=True)
sub.add_parser('root');sub.add_parser('shell')
s=sub.add_parser('screenshot');s.add_argument('path')
s=sub.add_parser('tap');s.add_argument('x',type=int);s.add_argument('y',type=int)
a=p.parse_args();base=['/opt/homebrew/bin/adb','-s',SERIAL]
if a.action in {'root','shell'}:
 cmd=sys.stdin.read()
 if a.action=='root':cmd='su -c '+shlex.quote(cmd)
 sys.exit(subprocess.call(base+['shell',cmd]))
if a.action=='screenshot':
 with Path(a.path).open('wb') as f:subprocess.run(base+['exec-out','screencap','-p'],stdout=f,check=True)
if a.action=='tap':
 subprocess.run(base+['shell','input','tap',str(a.x),str(a.y)],check=True);time.sleep(.6)
