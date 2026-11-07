"""Independent little-endian checkpoint reader for staging evidence (read-only)."""
from pathlib import Path
import hashlib,json,struct,sys
def decode(path):
 b=Path(path).read_bytes()
 assert 48<=len(b)<=8192 and b[:8]==b'OAMVCP1\0'
 version,size=struct.unpack_from('<II',b,8);assert version==1 and size==len(b)-48
 assert hashlib.sha256(b[48:]).digest()==b[16:48]
 at=48
 def take(fmt):
  nonlocal at
  v=struct.unpack_from('<'+fmt,b,at);at+=struct.calcsize('<'+fmt);return v[0] if len(v)==1 else v
 volume=b[at:at+32].hex();at+=32;runtime=b[at:at+32].hex();at+=32
 scene,region,generation=take('IIQ');idn=take('I');assert 0<idn<=127;identity=b[at:at+idn].decode('utf-8');at+=idn
 pose=take('5f');inside,skipped=take('II');count=take('I');assert count==3
 tutorials=[dict(zip(['id','active','fired','kills'],take('4I'))) for _ in range(count)]
 sv,wos,sword,cine,sword_get=take('4Ii');clock,serial,timers=take('QQI');assert sv==1 and timers==0 and sword==0 and sword_get==0 and skipped==cine
 assert at==len(b)
 return dict(file=str(path),bytes=len(b),file_sha256=hashlib.sha256(b).hexdigest(),version=version,volume_profile=volume,runtime_profile=runtime,scene=scene,region=region,generation=generation,identity=identity,pose=pose,inside_mask=inside,cinematic_skipped=skipped,tutorials=tutorials,lua=dict(version=sv,wos_flags=wos,sword_flags=sword,cinematic_flags=cine,sword_get=sword_get,clock_ms=clock,serial=serial,timer_count=timers))
if __name__=='__main__':print(json.dumps(decode(sys.argv[1]),indent=2))
