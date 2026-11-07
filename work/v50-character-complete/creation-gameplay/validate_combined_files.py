"""Independent byte reader: every final actual C fixture file, no live saves."""
from pathlib import Path
import struct,hashlib,json,zlib
ROOT=Path(__file__).resolve().parent
OUT=Path((ROOT/"latest-output.txt").read_text())
class R:
 def __init__(self,b,p=0):self.b=b;self.p=p
 def raw(self,n):
  assert n<=len(self.b)-self.p
  v=self.b[self.p:self.p+n];self.p+=n;return v
 def u(self):return struct.unpack("<I",self.raw(4))[0]
 def i(self):return struct.unpack("<i",self.raw(4))[0]
 def q(self):return struct.unpack("<Q",self.raw(8))[0]
 def f(self):return struct.unpack("<f",self.raw(4))[0]
def header(b,magic):
 assert 48<=len(b)<=32768 and b[:8]==magic
 v,n=struct.unpack_from("<II",b,8)
 assert v==1 and n==len(b)-48 and hashlib.sha256(b[48:]).digest()==b[16:48]
def nested(b):
 header(b,b"OAGPCP1\0")
 r=R(b,48)
 profiles=[r.raw(32).hex() for _ in range(3)]
 assert all(x!="00"*32 for x in profiles)
 assert r.u()==1417252 and r.u()==1262814 and r.q()==17
 assert r.u()==1790948 and r.u()==1789992 and r.u()==1360571
 assert r.q()==0x13300000007 and r.i()==7
 assert r.u()==613083 and r.i()==5 and r.u()==1
 identity=r.raw(r.u()).decode();assert identity=="scene1417252:player1:g17"
 pose=[r.f() for _ in range(5)]
 s=dict(zip(["inside","initialized","skipped","container_count","owned","equipped","door_open","secondary_disabled","compare_enabled"],[r.u() for _ in range(9)]))
 s["revision"]=r.q();s["quest_noops"]=r.q();assert r.u()==5
 tutorials=[dict(zip(["id","active","fired","kills"],[r.u() for _ in range(4)])) for _ in range(5)]
 lua=dict(zip(["version","wos_flags","sword_flags","cinematic_flags","sword_get"],[r.u() for _ in range(5)]))
 lua["clock"]=r.q();lua["serial"]=r.q();count=r.u();assert count<=2
 timers=[{"hash":r.u(),"due":r.q(),"serial":r.q(),"argc":r.u(),"item":r.i()} for _ in range(count)]
 assert r.p==len(b) and s["initialized"]==1 and lua["version"]==1 and s["skipped"]==lua["cinematic_flags"]
 for t in timers:
  assert t["hash"] in [151774118,165407883] and lua["clock"]<t["due"]<=lua["clock"]+15
 s.update(pose=pose,identity=identity,lua=lua,timers=timers,tutorials=tutorials)
 return s
def decode(p):
 b=p.read_bytes();header(b,b"OACGCP1\0");r=R(b,48)
 profilehash=r.raw(32);assert profilehash!=bytes(32);assert r.q()==17
 profile=r.raw(r.u());assert profile[:8]==b"OACREA1\0"
 pv,pn,crc,catalogue=struct.unpack_from("<4I",profile,8)
 assert pv==1 and pn==len(profile)-32 and crc==zlib.crc32(profile[32:])
 race,sex,preset,patron,phase,custom,default=profile[32:39]
 assert phase==2 and race<4 and sex<2 and patron<6
 rr=R(profile,32+53);transaction=rr.q();revision=rr.u();name=profile[32+65:].decode("utf-8");assert transaction
 skills=[r.i() for _ in range(9)]
 names=["patron","health","maxhealth","destiny_buff","destiny_identifier","started","passive","destiny_locked","fateweaver_locked","quest_stage","finalized","package4","stealth_registered","reckoning_registered","stealth","sees","reckoning"]
 owner=dict(zip(names,[r.u() for _ in names]));owner["revision"]=r.q();count=r.u()
 assert count==(165 if owner["package4"] else 162)
 items=[dict(zip(["type","count","slot","hidden"],[r.u(),r.u(),r.i(),r.u()])) for _ in range(count)]
 assert owner["destiny_buff"]==385357 and owner["destiny_identifier"]==9325294
 assert owner["started"]==owner["passive"]==owner["destiny_locked"]==owner["fateweaver_locked"]==owner["finalized"]==1
 assert owner["quest_stage"]==5 and owner["health"]<=owner["maxhealth"]
 assert owner["stealth_registered"]==owner["reckoning_registered"]==1
 assert items[5]=={"type":615585,"count":5,"slot":-1,"hidden":0}
 assert [x["type"] for x in items[6:11]]==[1321542,1321543,1330206,1330207,1381439]
 assert [x["slot"] for x in items[6:11]]==[0,0,0,1,0]
 game=nested(r.raw(r.u()));assert r.p==len(b)
 return {"file":p.name,"size":len(b),"sha256":hashlib.sha256(b).hexdigest(),"profile_hash":profilehash.hex(),"race":race,"sex":sex,"patron_index":patron,"name":name,"transaction":transaction,"catalogue_crc":catalogue,"owner":owner,"skills":skills,"item_count":count,"opening":game}
def f32(v):return struct.unpack("<f",struct.pack("<f",v))[0]
if __name__=="__main__":
 rows=[]
 for p in sorted(OUT.glob("r*-s*-p*.creation-gameplay-v1.bin")):
  x=decode(p);race,sex,pat=x["race"],x["sex"],x["patron_index"]
  assert p.name==f"r{race}-s{sex}-p{pat}.creation-gameplay-v1.bin"
  skills=[[10,20,0,0,0,0,10,0,0],[0,0,10,0,20,10,0,0,0],[10,0,0,20,0,0,0,10,0],[0,0,0,0,0,0,10,10,20]]
  assert x["skills"]==skills[race]
  definitions=json.loads((ROOT/"source-patrons.json").read_text())
  rec=next(q for q in definitions if q["id"]==x["owner"]["patron"])
  hp=100
  for op in rec["effects"]:
   if op["key"]==1657941:hp=int(f32(hp*op["value"] if op["op"]==1 else hp+op["value"]))
  assert x["owner"]["maxhealth"]==hp and x["owner"]["health"]==hp-11
  rows.append(x)
 assert len(rows)==48 and len({(r["race"],r["sex"],r["patron_index"]) for r in rows})==48
 atomic=decode(OUT/"atomic.creation-gameplay-v1.bin")
 assert atomic["opening"]["door_open"]==1 and atomic["opening"]["quest_noops"]==1 and atomic["owner"]["quest_stage"]==5
 result={"passed":True,"case_files":48,"source_unique_buffs":len({r["owner"]["patron"] for r in rows}),"atomic_opening_file":atomic,"all_case_receipts":rows,"scope":"actual private C production-runtime output; independent field-wise/checksum/source-data comparison"}
 (ROOT/"independent-combined-validation.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
 print(json.dumps({"passed":True,"case_files":48,"unique_buffs":result["source_unique_buffs"],"atomic_file_bytes":atomic["size"]}))
