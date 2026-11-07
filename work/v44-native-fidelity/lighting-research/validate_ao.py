from pathlib import Path
import re,ast,subprocess,json,ctypes,math
p=Path(__file__).parent
s=(p/'oa_native_ao.c').read_text();end=ast.literal_eval(re.search('const char \\*end=("(?:[^"\\\\]|\\\\.)*")',s).group(1));v=ast.literal_eval(re.search('static const char \\*vertex=("(?:[^"\\\\]|\\\\.)*")',s).group(1));(p/'ao-wrapper.vert').write_text(v)
results=[]
for m in [1910,1926]:
 x=(p/f'native-{m}.frag').read_text().replace('void main()','void oa_ao_compute()',1)+end;f=p/f'ao-gated-{m}.frag';f.write_text(x);r=subprocess.run(['glslangValidator',str(f)],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr;results.append(dict(module=m,exit=r.returncode))
(p/'ao-math-test.c').write_text('#include "oa_native_ao_math.h"\nint parameters(float *out,float *cut,const float *vp,int w,int h){return oa_native_ao_parameters(out,cut,vp,w,h);}\n')
r=subprocess.run(['clang','-std=c11','-Wall','-Wextra','-shared','-fPIC',str(p/'ao-math-test.c'),'-o',str(p/'ao-math-test.dylib')],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
lib=ctypes.CDLL(str(p/'ao-math-test.dylib'));fn=lib.parameters;ptr=ctypes.POINTER(ctypes.c_float);fn.argtypes=[ptr,ptr,ptr,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int
# GL perspective VP with translation, yaw/pitch and off-centre frustum.
# Build by numeric row multiplication, preserving column-majorfloat32 input.
def mul(a,b):return [[sum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
checks=[]
for w,h,n,f,px,py,ox,oy,yaw in [(1536,864,26.1861916,524288,1.311106,2.330855,0,0,.61),(1920,1080,5,100000,1.2,2.4,.1,-.07,.9),(1000,500,10,10000,1,2,0,0,0)]:
 A=(f+n)/(f-n);B=-2*n*f/(f-n);c=math.cos(yaw);s=math.sin(yaw)
 projection=[[px,0,ox,0],[0,py,oy,0],[0,0,A,B],[0,0,1,0]];view=[[c,0,-s,-30000],[0,1,0,1000],[s,0,c,70000],[0,0,0,1]]
 vp=mul(projection,view);fv=(ctypes.c_float*16)(*[vp[i][j] for j in range(4) for i in range(4)]);out=(ctypes.c_float*32)();cut=ctypes.c_float();assert fn(out,ctypes.byref(cut),fv,w,h)
 # FloatVP loses precision in large translations; bound depth B reconstruction
 # error against representable matrix rather than claiming bitwise reference.
 assert abs(out[16]-(-1-ox)/px)<1e-6;assert abs(out[17]-(1-oy)/py)<1e-6
 assert abs(out[18]-2/(w*px))<1e-8;assert abs(out[19]+2/(h*py))<1e-8
 assert abs(out[20]-(A+1)/2)<1e-6;assert abs(out[21]-B/2)<.02
 assert abs(cut.value-(out[20]+out[21]/6000))<1e-6
 checks.append(dict(w=w,h=h,expected_B=B/2,recovered_B=out[21],cut=cut.value,ray=out[16:20],projScale=out[6]))
# Orthographic input is rejected.
ident=(ctypes.c_float*16)(1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1);assert not fn(out,ctypes.byref(cut),ident,100,100)
validation=dict(gated_shaders=results,dynamic_projection_checks=checks,orthographic_rejected=True,gpu_execution=False)
(p/'ao-validation.json').write_text(json.dumps(validation,indent=2));print(json.dumps(validation,indent=2))
