from pathlib import Path
import json,struct,ctypes,math,hashlib
P=Path(__file__).resolve().parent;D=json.loads((P/'native-gbuffer-draws.json').read_text());H={x['buffer']:x for x in json.loads((P/'native-gbuffer-buffer-hashes.json').read_text())};M=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera/memory-52.bin').read_bytes();C=Path('/private/tmp/oa-dalentarth-20261105.gfxr');F=C.open('rb');cache={}
lib=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib');fn=lib.LZ4_decompress_safe;fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int
def payload(buf):
 if buf in cache:return cache[buf]
 if buf not in H:return None
 h=H[buf];F.seek(h['file_offset']);size,kind=struct.unpack('<QI',F.read(12));d=F.read(size);assert struct.unpack_from('<I',d)[0]==65543;assert struct.unpack_from('<Q',d,20)[0]==buf;n=struct.unpack_from('<Q',d,28)[0]
 if kind&0x80000000:
  out=ctypes.create_string_buffer(n);assert fn(d[36:],out,len(d)-36,n)==n;b=out.raw
 else:b=d[36:]
 assert len(b)==h['bytes'] and hashlib.sha256(b).hexdigest()==h['sha256'];cache[buf]=b;return b
points={'moss-root':(112.5,530.5),'booth':(850.5,489.5),'lamp':(1103.5,484.5)};hits={k:[] for k in points};fail=[]
for d in D:
 if d['phase']!=97:continue
 vb=d.get('vertex_bind',{});ib=d.get('index_bind',{});args=d['args']
 if not vb.get('pBuffers') or not ib:continue
 vbuf=vb['pBuffers'][0];stride=vb['pStrides'][0]
 if stride<12:continue
 v=payload(vbuf);ind=payload(ib['buffer'])
 if v is None or ind is None:continue
 u=next((q for q in d['uniforms'] if q['binding']==68 and q['memory']==52),None)
 if not u:continue
 # The selected opaque families use rows8..11 as object->clip. Terrain is excluded.
 if d['vs'] in [791,785,893] or any(q['binding']==69 for q in d['uniforms']):continue
 mat=struct.unpack_from('<16f',M,u['offset']+128);base=vb['pOffsets'][0];count=(len(v)-base)//stride;pos=[struct.unpack_from('<3f',v,base+k*stride) for k in range(count)]
 clips=[tuple(sum(p[k]*mat[k*4+j] for k in range(3))+mat[12+j] for j in range(4)) for p in pos];proj=[((q[0]/q[3]+1)*768,(1-q[1]/q[3])*432,q[2]/q[3],q[3]) if q[3]>0 else None for q in clips]
 positive=[p for p in proj if p];
 if not positive:continue
 bbox=[min(p[0] for p in positive),min(p[1] for p in positive),max(p[0] for p in positive),max(p[1] for p in positive)]
 relevant={k:p for k,p in points.items() if bbox[0]<=p[0]<=bbox[2] and bbox[1]<=p[1]<=bbox[3]}
 if not relevant:continue
 code='H' if ib['indexType']=='VK_INDEX_TYPE_UINT16' else 'I';isz=struct.calcsize(code);indices=struct.unpack_from('<'+str(args['indexCount'])+code,ind,ib['offset']+args['firstIndex']*isz);off=args['vertexOffset'];best={k:None for k in relevant}
 for t in range(0,len(indices)-2,3):
  ix=[indices[t+z]+off for z in range(3)]
  if max(ix)>=len(proj):continue
  a,b,c=[proj[z] for z in ix]
  if a is None or b is None or c is None:continue
  area=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
  if abs(area)<1e-10:continue
  for k,(x,y) in relevant.items():
   q=((b[0]-x)*(c[1]-y)-(b[1]-y)*(c[0]-x))/area;r=((c[0]-x)*(a[1]-y)-(c[1]-y)*(a[0]-x))/area;s=1-q-r
   if min(q,r,s)<-1e-6:continue
   z=q*a[2]+r*b[2]+s*c[2]
   if z<0 or z>1:continue
   w=1/(q/a[3]+r/b[3]+s/c[3])
   if best[k] is None or z<best[k]['depth']:best[k]={'triangle':t//3,'indices':ix,'depth':z,'clipW':w,'barycentric':[q,r,s]}
 for k,h in best.items():
  if h:h.update(draw=d['index'],vs=d['vs'],pipeline=d['pipeline'],vertex_buffer=vbuf,index_buffer=ib['buffer'],vertex_sha256=H[vbuf]['sha256'],index_sha256=H[ib['buffer']]['sha256'],bbox=bbox,world_matrix=d['world_matrix_row_major']);hits[k].append(h)
for k in hits:hits[k].sort(key=lambda q:q['depth'])
(P/'native-three-point-hits.json').write_text(json.dumps({'points':points,'hits':hits,'limits':'Geometric coverage before alpha/cull/depth/stencil; rigid opaque VS591/903 exact, VS877 local wind omitted. No GPU replay.'},indent=2))
for k,h in hits.items():print(k,[(a['draw'],a['vs'],a['vertex_buffer'],round(a['clipW'],2)) for a in h[:8]])
