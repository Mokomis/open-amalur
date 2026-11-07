"""Read-only snapshot of actual registered native static collections (same game build)."""
import ctypes as c,subprocess,json,struct,hashlib,time
from pathlib import Path
Q=Path(__file__).resolve().parent
pro=json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',"Get-Process koa | Select-Object Id,Path,@{N='base';E={$_.MainModule.BaseAddress.ToInt64()}} | ConvertTo-Json -Compress"],text=True))
assert isinstance(pro,dict),pro
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(Path(pro['Path']).read_bytes())=='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
k=c.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[c.c_uint,c.c_int,c.c_uint];k.OpenProcess.restype=c.c_void_p;k.ReadProcessMemory.argtypes=[c.c_void_p,c.c_void_p,c.c_void_p,c.c_size_t,c.POINTER(c.c_size_t)];k.CloseHandle.argtypes=[c.c_void_p]
h=k.OpenProcess(0x410,0,pro['Id']);assert h
try:
 def read(a,n=4):
  b=c.create_string_buffer(n);nr=c.c_size_t();assert k.ReadProcessMemory(h,a,b,n,c.byref(nr)) and nr.value==n,(hex(a),n,c.get_last_error());return b.raw
 def u(a):return struct.unpack('<I',read(a))[0]
 def va(a):return pro['base']+a-0x400000
 be=u(va(0x019fdfb4));handle=u(be+0xa90);table=u(be+0x3f8);config=u(table+4*(handle&65535));count=u(config+0x70);assert 0<count<1024
 ids=[];rows=[]
 for i in range(count):
  ptr=u(u(config+0x6c)+i*4);b=read(ptr,72);sid=struct.unpack_from('<I',b,4)[0];name='descriptor-%02d.bin'%i;(Q/name).write_bytes(b);ids.append(sid);rows.append(dict(index=i,address=hex(ptr),space_id=sid,dump=name,sha256=sha(b),group_counts=[struct.unpack_from('<I',b,8+16*g)[0] for g in range(4)]))
 groups=[]
 for i in range(u(config+0x3c)):
  ptr=u(u(config+0x38)+i*4);groups.append(dict(index=i,address=hex(ptr),space_id=u(ptr+4)))
 b=read(config,0xe0);(Q/'render-config.bin').write_bytes(b)
 cameras=[];camera_table=u(be+0x5f0)
 for ci in range(16):
  try:
   ca=u(camera_table+ci*4)
   if ca<0x10000:continue
   data=read(ca,0x380);sid=struct.unpack_from('<I',data,0x360)[0];xyz=struct.unpack_from('<3f',data,4)
   if sid not in [431646,431650,431638,0]:continue
   (Q/('camera-%02d.bin'%ci)).write_bytes(data);cameras.append(dict(slot=ci,address=hex(ca),space_id=sid,cull_xyz=xyz,sha256=sha(data)))
  except AssertionError:pass
 for entry in groups:
  data=read(int(entry['address'],16),0x100);name='spacegroup-%02d.bin'%entry['index'];(Q/name).write_bytes(data);entry['dump']=name;entry['sha256']=sha(data)

 report=dict(process=pro,read_only=True,openprocess_access='PROCESS_VM_READ|PROCESS_QUERY_INFORMATION only; no writes/attach/input',time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),backend=hex(be),main_config_handle=hex(handle),config=hex(config),config_sha256=sha(b),quality_enabled=read(va(0x019661f6),1)[0],quality_squared=struct.unpack('<f',read(va(0x019662d8)))[0],camera_table=hex(camera_table),cameras=cameras,registered_static_spaces=ids,static_descriptors=rows,registered_space_visibility_groups=groups,source198_space=431642,source198_collection_registered=431642 in ids,source_note='Same cs15032 executable SHA; desktop screenshot confirms paused bridge. Registered != necessarily admitted individual draw. No hardcoded runtime whitelist implied.')
 (Q/'registered-collections.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
finally:k.CloseHandle(h)
