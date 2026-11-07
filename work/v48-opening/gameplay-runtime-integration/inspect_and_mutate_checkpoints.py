"""Independent portable byte decode + checksum-aware typed corruption tests.
Only staged private fixtures and staged executable are used, never live saves."""
from pathlib import Path
import struct,hashlib,json,subprocess
ROOT=Path(__file__).resolve().parent
OUT=Path((ROOT/"latest-output.txt").read_text())
ASSETS=ROOT.parent/"runtime-integration/assets"
EXE=ROOT/"build/oa-opening-gameplay-test.exe"
class Decoder:
 def __init__(self,b):self.b=b;self.p=48;self.offsets={}
 def raw(self,n):v=self.b[self.p:self.p+n];assert len(v)==n;self.p+=n;return v
 def u(self,name=None):
  if name:self.offsets[name]=self.p
  return struct.unpack("<I",self.raw(4))[0]
 def q(self,name=None):
  if name:self.offsets[name]=self.p
  return struct.unpack("<Q",self.raw(8))[0]
 def f(self):return struct.unpack("<f",self.raw(4))[0]
def decode(path):
 b=path.read_bytes();assert len(b)<=8192
 magic,v,n,digest=struct.unpack("<8sII32s",b[:48])
 assert magic==b"OAGPCP1\0" and v==1 and n==len(b)-48 and hashlib.sha256(b[48:]).digest()==digest
 d=Decoder(b)
 r={"path":str(path),"size":len(b),"sha256":hashlib.sha256(b).hexdigest(),"profiles":[d.raw(32).hex() for _ in range(3)]}
 r.update(scene=d.u("scene"),region=d.u("region"),generation=d.q("generation"),gor=d.u("gor"),container=d.u("container"),itemtype=d.u("itemtype"),item_instance=d.q("item_instance"),item_index=d.u("item_index"),quest=d.u("quest"),quest_stage=struct.unpack("<i",struct.pack("<I",d.u("quest_stage")))[0],tutorials_enabled=d.u("tutorials_enabled"))
 r["identity"]=d.raw(d.u()).decode()
 r["pose"]=[d.f() for _ in range(5)]
 for name in ["inside","initialized","skipped","container_count","owned","equipped","door_open","secondary_disabled","compare_enabled"]:r[name]=d.u(name)
 r["revision"]=d.q("revision");r["quest_noops"]=d.q("quest_noops")
 r["tutorials"]=[]
 assert d.u("tutorial_count")==5
 for i in range(5):r["tutorials"].append({name:d.u(f"tutorial{i}.{name}") for name in ["id","active","fired","kills"]})
 r["lua"]={name:d.u("lua."+name) for name in ["version","wos_flags","sword_flags","cinematic_flags","sword_get"]}
 r["lua"].update(clock_ms=d.q("lua.clock_ms"),serial=d.q("lua.serial"))
 r["lua"]["timers"]=[]
 count=d.u("lua.timer_count")
 assert count<=128
 for i in range(count):
  r["lua"]["timers"].append({"hash":d.u(f"timer{i}.hash"),"due_ms":d.q(f"timer{i}.due_ms"),"serial":d.q(f"timer{i}.serial"),"argc":d.u(f"timer{i}.argc"),"item_index":d.u(f"timer{i}.item_index")})
 assert d.p==len(b)
 return r,d.offsets
if __name__=="__main__":
 records=[]
 for name in ["main","timers","disabled"]:
  record,_=decode(OUT/(name+".opening-gameplay-v1.bin"));records.append(record)
 timer=OUT/"timers.opening-gameplay-v1.bin"
 baseline=timer.read_bytes();record,off=decode(timer)
 assert record["lua"]["clock_ms"]==0 and len(record["lua"]["timers"])==2 and record["owned"]==1 and record["equipped"]==0 and record["quest_stage"]==-1
 assert [t["hash"] for t in record["lua"]["timers"]]==[151774118,165407883]
 assert [t["due_ms"] for t in record["lua"]["timers"]]==[15,15]
 target=OUT/"mutant.opening-gameplay-v1.bin"
 cases=[
 ("scene",0,"I"),("region",0,"I"),("generation",18,"Q"),("gor",0,"I"),("container",0,"I"),("itemtype",0,"I"),("item_instance",0,"Q"),("item_index",8,"I"),("quest",0,"I"),("quest_stage",25,"I"),("tutorials_enabled",0,"I"),
 ("inside",7,"I"),("initialized",0,"I"),("skipped",0,"I"),("container_count",1,"I"),("owned",0,"I"),("equipped",1,"I"),("door_open",1,"I"),("secondary_disabled",0,"I"),("compare_enabled",1,"I"),
 ("lua.version",2,"I"),("lua.wos_flags",0,"I"),("lua.sword_flags",5,"I"),("lua.cinematic_flags",0,"I"),("lua.sword_get",0,"I"),
 ("lua.clock_ms",9007194959773696,"Q"),("lua.serial",0,"Q"),("lua.timer_count",129,"I"),
 ("timer0.hash",123,"I"),("timer0.due_ms",0,"Q"),("timer0.due_ms",16,"Q"),("timer0.serial",0,"Q"),("timer0.argc",0,"I"),("timer0.item_index",8,"I"),
 ("timer1.hash",151774118,"I"),("timer1.serial",1,"Q"),("timer1.argc",1,"I"),("timer1.item_index",7,"I"),
 ("tutorial0.id",999,"I"),("tutorial0.active",2,"I"),("tutorial0.fired",2,"I"),("tutorial_count",6,"I"),
 ]
 results=[]
 # Valid pending authored timers reload first, then checksum-aware corruptions.
 r=subprocess.run([str(EXE),"--load-check",str(ASSETS),str(timer),"0"],capture_output=True,text=True,timeout=30)
 assert r.returncode==0,(r.stdout,r.stderr)
 for key,value,fmt in cases:
  b=bytearray(baseline);struct.pack_into("<"+fmt,b,off[key],value);b[16:48]=hashlib.sha256(b[48:]).digest();target.write_bytes(b)
  before=target.read_bytes()
  r=subprocess.run([str(EXE),"--load-check",str(ASSETS),str(target),"1"],capture_output=True,text=True,timeout=30)
  assert r.returncode==0,(key,value,r.stdout,r.stderr)
  assert target.read_bytes()==before
  results.append({"field":key,"value":value,"passed":True,"rejection":r.stderr.strip()})
 # Three pinned profile hashes are independently tested despite valid checksums.
 for k in range(3):
  b=bytearray(baseline);b[48+k*32]^=1;b[16:48]=hashlib.sha256(b[48:]).digest();target.write_bytes(b)
  r=subprocess.run([str(EXE),"--load-check",str(ASSETS),str(target),"1"],capture_output=True,text=True,timeout=30)
  assert r.returncode==0,(k,r.stdout,r.stderr)
  results.append({"profile":k,"passed":True,"rejection":r.stderr.strip()})
 (ROOT/"checkpoint-byte-validation.json").write_text(json.dumps({"passed":True,"records":records,"typed_checksum_valid_mutation_cases":len(results),"cases":results,"offsets":off,"source_fixtures_only":True},indent=2))
 print(json.dumps({"passed":True,"decoded_files":len(records),"typed_checksum_valid_mutation_cases":len(results)}))
