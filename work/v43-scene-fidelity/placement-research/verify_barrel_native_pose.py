"""Recheck native barrel pose output against independent standard quaternion math."""
from pathlib import Path
import hashlib,struct,json,math,subprocess,sys
w=Path(__file__).resolve().parent;r=w.parents[2]
exe=r/'work/v30-engine/koa.exe';fb=r/'work/v20-inputs/initial_0.pak/1425589.fab_bxml'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(exe)=='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
assert sha(fb)=='b51f2dfc5980dfc025ce5364ab36d9a9bb15ab018bf3db472f6a8738b4da2a39'
p=w/'barrel-native-pose-output.bin'
if '--run' in sys.argv:
 p=w/'barrel-native-pose-recheck.bin'
 z=subprocess.run([str(w/'barrel_native_pose.exe'),str(exe),str(fb),str(p)],capture_output=True,text=True,timeout=15)
 assert z.returncode==0,(z.returncode,z.stdout,z.stderr)
raw=fb.read_bytes();out=p.read_bytes();n=struct.unpack_from('<I',out)[0];assert n==4 and len(out)==4+n*112
pose=28+struct.unpack_from('<i',raw,28)[0];parent=32+struct.unpack_from('<i',raw,32)[0]
assert pose==100 and parent==292 and struct.unpack_from('<h',raw,parent+4)[0]==0
q=struct.unpack_from('<4f',raw,pose+2*48);assert struct.unpack_from('<3f',raw,pose+2*48+16)==(0,0,0)
assert struct.unpack_from('<3f',raw,pose+2*48+32)==(1,1,1)
assert struct.unpack_from('<4f',raw,pose)==(0,0,0,1)
mat=struct.unpack_from('<16f',out,4+2*112+48);col=[mat[c*4+rr]for rr in range(4)for c in range(4)]
def matrix(q):
 x,y,z,v=q;inv=1/math.sqrt(sum(a*a for a in q));x*=inv;y*=inv;z*=inv;v*=inv
 return [1-2*(y*y+z*z),2*(x*y-z*v),2*(x*z+y*v),0,2*(x*y+z*v),1-2*(x*x+z*z),2*(y*z-x*v),0,2*(x*z-y*v),2*(y*z+x*v),1-2*(x*x+y*y),0,0,0,0,1]
direct=matrix(q);conj=matrix([-q[0],-q[1],-q[2],q[3]])
a=max(abs(x-y)for x,y in zip(col,direct));b=max(abs(x-y)for x,y in zip(col,conj));assert a>.5 and b<1e-6
row=dict(native_source_sha256=sha(exe),source_fab_sha256=sha(fb),joints=n,native_quaternion_unchanged=list(struct.unpack_from('<4f',out,4+2*112+16))==list(q),column_vector_local_bind=col,direct_error=a,conjugated_error=b,point_100_x=[100*col[0],100*col[4],100*col[8]],scope='Standalone original pose arithmetic; no observed original draw')
assert row['native_quaternion_unchanged']
(w/'barrel-native-independent-validation.json').write_text(json.dumps(row,indent=2))
print(json.dumps(row,indent=2))
