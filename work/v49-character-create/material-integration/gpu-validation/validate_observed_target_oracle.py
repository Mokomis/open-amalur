"""Independent source oracle using separately observed backend target rounding."""
from pathlib import Path
import runpy,contextlib,io,json,hashlib
import numpy as np
P=Path(__file__).resolve().parent
with contextlib.redirect_stdout(io.StringIO()):d=runpy.run_path(str(P/'validate_source_oracle.py'))
f=np.float32;N=d['N'];V=d['V'];out=[]
for c in d['cases']:
 if c['diagnostic_normal']:continue
 facing=np.clip(np.sum(N*V,axis=-1,dtype=np.float32),f(0),f(1))
 rim=np.clip((f(1.4) if c['fresnel_on'] else f(0))*np.power(f(1)-facing,f(2.4)),f(0),f(1))
 base=(d['D']+f(.15)*rim[...,None])*d['VC']*f(c['alpha'])
 raw=np.clip(d['CUBE']*f(c['alpha'])*base,f(0),f(1))
 h=raw.astype(np.float16)
 h=np.where(h.astype(np.float32)>raw,np.nextafter(h,np.zeros_like(h),dtype=np.float16),h).astype(np.float32)
 rgb=np.rint(h*f(255)).astype(np.uint8)
 exp=np.concatenate([rgb,np.full((32,32,1),255,dtype=np.uint8)],axis=-1)
 actual=np.frombuffer((P/c['file']).read_bytes(),dtype=np.uint8).reshape(32,32,4)
 delta=np.abs(actual.astype(np.int16)-exp.astype(np.int16))
 name=c['file'].replace('.rgba','-observed-target-oracle.rgba');(P/name).write_bytes(exp.tobytes())
 out.append({'id':c['id'],'oracle_file':name,'oracle_sha256':hashlib.sha256(exp.tobytes()).hexdigest(),'center_RGBA8':exp[16,16].tolist(),'center_G2_half':h[16,16].tolist(),'max_abs_code_delta':int(delta.max()),'mismatched_channels':int(np.count_nonzero(delta))})
summary={'case_count':len(out),'rounding_model':'Nonnegative0..1 G2 float32-to-half towardzero; supported by all3 discriminating direct RGBA16F target and packHalf probes on this actual ANGLE/NVIDIA backend. Not claimed universal/native-opening capture rounding.','source_math':'IndependentPS352 source arithmetic unchanged; only target HALF rounding differs from original idealRNE oracle. Shader final roundEvenRGBA8 remains.','max_abs_code_delta':max(x['max_abs_code_delta'] for x in out),'mismatched_channels':sum(x['mismatched_channels'] for x in out),'compared_channels':24*32*32*4,'cases':out}
summary['all_material_pixels_exact']=summary['mismatched_channels']==0
assert summary['max_abs_code_delta']<=1
(P/'observed-target-oracle-validation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='cases'}))
