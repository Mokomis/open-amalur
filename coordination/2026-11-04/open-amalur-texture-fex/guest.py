"""Bounded request to DroidDeck's existing guest command bridge; retains evidence."""
import base64,json,shlex,subprocess,sys,time,uuid
from pathlib import Path
serial='99cc517a';root='/data/user/0/com.droiddeck.launcher/files/session/agent'
request=json.load(sys.stdin);rid='oa-'+uuid.uuid4().hex
out=Path(__file__).parent/'evidence/guest';out.mkdir(exist_ok=True)
(out/(rid+'-request.json')).write_text(json.dumps(request,indent=2))
payload=base64.b64encode(json.dumps(request).encode()).decode()
cmd=f"printf %s {shlex.quote(payload)} | base64 -d > {root}/{rid}.tmp && chown 10307:10307 {root}/{rid}.tmp && chmod 600 {root}/{rid}.tmp && mv {root}/{rid}.tmp {root}/req/{rid}.json"
def rootcmd(s):return ['adb','-s',serial,'shell','su -c '+shlex.quote(s)]
subprocess.run(rootcmd(cmd),check=True)
deadline=time.monotonic()+min(60,float(request.get('timeout',15))+10)
while time.monotonic()<deadline:
 r=subprocess.run(rootcmd(f'test -f {root}/resp/{rid}.json && cat {root}/resp/{rid}.json'),capture_output=True,text=True)
 if r.returncode==0 and r.stdout.strip():
  data=json.loads(r.stdout);(out/(rid+'-response.json')).write_text(json.dumps(data,indent=2))
  print(json.dumps(data,indent=2));sys.exit(0 if data.get('ok') else 1)
 time.sleep(.3)
raise TimeoutError('No bridge response; request ID '+rid+' retained. Check daemon and ownership before another attempt.')
