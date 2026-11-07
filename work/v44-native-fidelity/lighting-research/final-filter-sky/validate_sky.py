from pathlib import Path
import subprocess,ctypes,struct,json,hashlib
p=Path(__file__).parent
(p/'sky-geometry-test.c').write_text('#include "oa_native_sky_geometry.h"\nvoid geometry(float *v,uint16_t *i){oa_native_sky_geometry((float(*)[5])v,i);}\n')
r=subprocess.run(['clang','-std=c11','-Wall','-Wextra','-shared','-fPIC',str(p/'sky-geometry-test.c'),'-o',str(p/'sky-geometry-test.dylib')],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
lib=ctypes.CDLL(str(p/'sky-geometry-test.dylib'));lib.geometry.argtypes=[ctypes.POINTER(ctypes.c_float),ctypes.POINTER(ctypes.c_uint16)]
v=(ctypes.c_float*(576*5))();i=(ctypes.c_uint16*1722)();lib.geometry(v,i)
vb=bytes(v);ib=bytes(i);native=(p/'sky-vertices.bin').read_bytes();natives=struct.unpack('<2880f',native);diff=[(j,x,natives[j]) for j,x in enumerate(v) if x!=natives[j]]
print('geometry float differences',len(diff),'max',max((abs(x-y) for _,x,y in diff),default=0),'first',diff[:20]);print('index exact',ib==(p/'sky-indices.bin').read_bytes()[:1722*2])
# Native x87 converts individual sin/cos results to float before multiplication.
# A procedural mesh must agree within representable float arithmetic, rather
# than replacing its positions with a new guessed unit dome.
assert len(diff)==0,(len(diff),diff[:4]);assert ib==(p/'sky-indices.bin').read_bytes()[:1722*2]
d=dict(procedural_vertices_exact_bytes=vb==native,indices_exact_active_bytes=True,vertices_sha256=hashlib.sha256(vb).hexdigest(),index_sha256=hashlib.sha256(ib).hexdigest(),gpu_execution=False)
(p/'sky-geometry-validation.json').write_text(json.dumps(d,indent=2))
