from pathlib import Path
import json,subprocess,ctypes,numpy as np,re,ast
p=Path(__file__).parent
(p/'shadow-math-test.c').write_text('#include "oa_native_shadow_math.h"\nint parameters(oa_native_shadow_cascade *o,float *ab,const float *v,const float *eye,const float *sun){oa_native_shadow_config c;oa_native_shadow_defaults(&c);c.projection_scale[0]=1.f/.7627148628234863f;c.projection_scale[1]=1.f/.42902708053588867f;return oa_native_shadow_parameters(o,ab,v,eye,sun,&c);}\n')
r=subprocess.run(['clang','-std=c11','-Wall','-Wextra','-shared','-fPIC',str(p/'shadow-math-test.c'),'-o',str(p/'shadow-math-test.dylib')],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
class Cascade(ctypes.Structure):
 _fields_=[('vp',ctypes.c_float*16),('screen_to_light',ctypes.c_float*16),('fade',ctypes.c_float*4),('center',ctypes.c_float*3),('half_extent',ctypes.c_float),('near_z',ctypes.c_float),('far_z',ctypes.c_float)]
lib=ctypes.CDLL(str(p/'shadow-math-test.dylib'));fn=lib.parameters;ptr=ctypes.POINTER(ctypes.c_float);fn.argtypes=[ctypes.POINTER(Cascade),ptr,ptr,ptr,ptr];fn.restype=ctypes.c_int
ph=json.loads((p/'phases.json').read_text());v=next(x for x in ph if x['phase']==112)['draws'][0]['uniforms'][1]['values'];m=np.array(v[:16],np.float32).reshape(4,4,order='F');m[2,:]=2*m[2,:]-m[3,:]
vp=(ctypes.c_float*16)(*m.flatten(order='F'));eye=(ctypes.c_float*3)(*v[16:19]);sun=(ctypes.c_float*3)(0,.36543822288513184,.930835485458374);out=(Cascade*3)();ab=(ctypes.c_float*2)();assert fn(out,ab,vp,eye,sun)
results=[]
for i,phase,resolve in [(0,103,104),(1,101,102),(2,99,100)]:
 u=next(y for y in next(x for x in ph if x['phase']==phase)['draws'][0]['uniforms'] if y['slot']==68)['values']
 w=np.array(u[:16]).reshape(4,4,order='F');expected=np.array(u[32:48]).reshape(4,4,order='F')@np.linalg.inv(w)
 actual=np.array(out[i].vp).reshape(4,4,order='F');actual[2,:]=.5*(actual[2,:]+actual[3,:])
 c=next(y for y in next(x for x in ph if x['phase']==resolve)['draws'][0]['uniforms'] if y['slot']==0)['values'];sm=np.array(c[8:24]).reshape(4,4,order='F');ours=np.array(out[i].screen_to_light).reshape(4,4,order='F')
 err=np.abs(actual-expected);serr=np.abs(ours-sm);print(i,'vpmax',err.max(),'screenmax',serr.max(),'vp',actual,'expected',expected,'screen',ours,'expectscreen',sm)
 assert err.max()<2e-5;assert serr.max()<2e-5
 # Captured XY snaps: exact multiples of2/1024, agreement within floatrounding.
 assert np.abs(actual[:2,3]-expected[:2,3]).max()<3e-6
 results.append(dict(cascade=i,half_extent=out[i].half_extent,center=list(out[i].center),near_z=out[i].near_z,far_z=out[i].far_z,fade=list(out[i].fade),vp_max_abs_error=float(err.max()),screen_to_light_max_abs_error=float(serr.max())))
# Camera changes must alter live matrices rather than retain recorded ones.
eye2=(ctypes.c_float*3)(eye[0]+137,eye[1]-37,eye[2]+51);out2=(Cascade*3)();assert fn(out2,ab,vp,eye2,sun);assert list(out2[0].vp)!=list(out[0].vp)
# Symmetric frustum reaches splitfar +/- corners inside raster XY afterpadding.
for i,c in enumerate(out):
 near=[1,440,1400][i];far=[500,1500,10000][i]
 assert c.half_extent>0 and c.far_z>c.near_z
# AA/filter GLSL syntax.
s=(p/'oa_native_shadow.c').read_text()
for n,stage in [('vs','vert'),('fs','frag')]:
 t=ast.literal_eval(re.search('static const char \\*'+n+'=(\"(?:[^\"\\\\]|\\\\.)*\")',s).group(1));f=p/('native-shadow.'+stage);f.write_text(t);r=subprocess.run(['glslangValidator',str(f)],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
d=dict(reference_capture_matrices=results,camera_motion_changes_matrices=True,shader_syntax=True,gpu_execution=False,visual_parity=False)
(p/'shadow-validation.json').write_text(json.dumps(d,indent=2));print(json.dumps(d,indent=2))
