from pathlib import Path
import json,struct,math,ctypes,hashlib,numpy as np
p=Path(__file__).parent;r=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera');idx=json.loads((r/'capture-index.json').read_text());phases=json.loads((p.parent/'phases.json').read_text());draws={d['index']:d for ph in phases for d in ph['draws'] if d['modules']==[791,792]};states={};records=[]
for ln,l in enumerate(open('/private/tmp/oa-dalentarth.jsonl')):
 if ln==0:continue
 j=json.loads(l);i=j['index'];f=j.get('vkFunc',{});n=f.get('name','');a=f.get('args',{})
 if n=='vkCmdBindVertexBuffers2':states[a['commandBuffer']]=a
 if i in draws:
  s=states[a['commandBuffer']];d=draws[i];records.append(dict(index=i,buffer=s['pBuffers'][0],offset=s['pOffsets'][0],stride=s['pStrides'][0],uniforms=d['uniforms'],sampled=d['sampled']))
 if i>max(draws):break
lib=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib');fn=lib.LZ4_decompress_safe;fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int
cross=lambda a,b:(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]);norm=lambda a:tuple(x/math.sqrt(sum(y*y for y in a)) for x in a)
errors=[];buffers=[]
with open('/private/tmp/oa-dalentarth-20261105.gfxr','rb') as cap:
 for b in sorted(set(d['buffer'] for d in records)):
  mem,off=idx['buffer_memory'][str(b)];fill=[f for f in idx['fills'] if f['memory']==mem][-1];cap.seek(fill['file_offset']);stored=cap.read(fill['stored_size']);buf=ctypes.create_string_buffer(fill['size']);assert fn(stored[36:],buf,len(stored)-36,fill['size'])==fill['size'];raw=buf.raw[off:off+idx['buffers'][str(b)]['size']];assert len(raw)%48==0
  (p/f'terrain-{b}-vertices.bin').write_bytes(raw);errs=[]
  for offset in range(0,len(raw),48):
   v=struct.unpack_from('<12f',raw,offset);n,t,bn=v[3:6],v[6:9],v[9:12];nn=np.asarray(n,dtype=np.float32);seed=np.asarray((1,0,nn[0]/nn[2]),dtype=np.float32);tt=seed-nn*np.dot(seed,nn);tt/=np.sqrt(np.dot(tt,tt));bb=np.cross(nn,tt);e=max(abs(x-y) for x,y in zip(tuple(tt)+tuple(bb),t+bn));errs.append(e)
  errors+=errs;buffers.append(dict(buffer=b,memory=mem,vertices=len(raw)//48,fill=fill,sha256=hashlib.sha256(raw).hexdigest(),max_component_error=float(max(errs))))
report=dict(terrain_draws=len(records),unique_buffers=len(buffers),vertices=len(errors),formula='seed=vec3(1,0,N.x/N.z);T=normalize(seed-N*dot(seed,N));B=cross(N,T); all operations float32',max_component_error=float(max(errors)),buffers=buffers,source_correlated=True)
(p/'terrain-basis-validation.json').write_text(json.dumps(report,indent=2));(p/'terrain-draw-contracts.json').write_text(json.dumps(records,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='buffers'},indent=2))
