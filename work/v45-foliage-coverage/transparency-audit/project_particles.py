from pathlib import Path
import json,struct,ctypes
P=Path(__file__).resolve().parent;C=Path('/private/tmp/oa-dalentarth-20261105.gfxr');R=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera');J=json.loads((R/'capture-index.json').read_text());d=next(f for f in J['fills'] if f['memory']==129)
f=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib').LZ4_decompress_safe;f.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];f.restype=ctypes.c_int
with C.open('rb') as c:c.seek(d['file_offset']);b=c.read(d['stored_size'])
out=ctypes.create_string_buffer(d['size']);assert f(b[36:],out,len(b)-36,d['size'])==d['size'];V=out.raw;(P/'memory-129.bin').write_bytes(V);M=(R/'memory-52.bin').read_bytes();D=json.loads((P/'phase111-bindings.json').read_text());points={'980210':(980.5,210.5),'50035':(500.5,35.5),'800150':(800.5,150.5)};rows=[]
for d in D:
 if d['vs'] not in [1039,1041,1043]:continue
 vb=d['vertex_bind'];assert vb['pBuffers'][0]==128 and vb['pStrides'][0]==24;offset=vb['pOffsets'][0]+d['args']['firstVertex']*24;nv=d['args']['vertexCount'];p=[struct.unpack_from('<3f',V,offset+24*k) for k in range(nv)];uv=[struct.unpack_from('<2f',V,offset+24*k+12) for k in range(nv)];col=[struct.unpack_from('<4B',V,offset+24*k+20) for k in range(nv)];u=next(u for u in d['uniforms'] if u['binding']==68);mat=struct.unpack_from('<16f',M,u['offset']+128);clip=[tuple(sum(v[k]*mat[k*4+j] for k in range(3))+mat[12+j] for j in range(4)) for v in p];sp=[((v[0]/v[3]+1)*768,(1-v[1]/v[3])*432,v[2]/v[3],v[3]) if v[3]>0 else None for v in clip];hits=[]
 for at in range(0,nv,3):
  a,b,c=sp[at:at+3]
  if a is None or b is None or c is None:continue
  area=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
  if abs(area)<1e-12:continue
  for label,(x,y) in points.items():
   q=((b[0]-x)*(c[1]-y)-(b[1]-y)*(c[0]-x))/area;r=((c[0]-x)*(a[1]-y)-(c[1]-y)*(a[0]-x))/area;s=1-q-r
   if min(q,r,s)<0:continue
   z=q*a[2]+r*b[2]+s*c[2]
   if not 0<=z<=1:continue
   iw=q/a[3]+r/b[3]+s/c[3];wts=[q/a[3]/iw,r/b[3]/iw,s/c[3]/iw];tu=[sum(wts[k]*uv[at+k][j] for k in range(3)) for j in range(2)];vc=[sum(wts[k]*col[at+k][j]/255 for k in range(3)) for j in range(4)];hits.append({'point':label,'triangle':at//3,'depth':z,'clipW':1/iw,'UV':tu,'VC':vc})
 positive=[v for v in sp if v];bbox=[min(v[0] for v in positive),min(v[1] for v in positive),max(v[0] for v in positive),max(v[1] for v in positive)] if positive else None;dyn=[struct.unpack_from('<4f',M,u['offset']+r*16) for r in [13,14,15]];rows.append({'draw':d['index'],'vs':d['vs'],'ps':d['ps'],'pipeline':d['pipeline'],'vertex_buffer_offset':offset,'vertices':nv,'bbox':bbox,'hits':hits,'dynamic_tint_luminance':dyn,'world_positions':p,'UV':uv,'RGBA8':col,'nativeWVP':mat})
(P/'particle-coverage.json').write_text(json.dumps(rows,indent=2))
for r in rows:
 if r['hits']:print(r['draw'],r['vs'],[(h['point'],h['triangle'],round(h['clipW'],3),h['UV'],h['VC']) for h in r['hits']])
