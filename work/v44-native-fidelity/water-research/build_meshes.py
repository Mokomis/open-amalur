from pathlib import Path
import json,struct,math,hashlib
R=Path(__file__).resolve().parent;A=json.loads((R/'active-water-bindings.json').read_text());matches={d['draw']:d for d in json.loads((R/'material-capture-match.json').read_text())};O=R/'meshes';O.mkdir(exist_ok=True);manifest=[]
def transform(v,m,translate):return tuple(sum(v[j]*m[j*4+k] for j in range(3))+(m[12+k] if translate else 0) for k in range(3))
def norm(v):
 l=math.sqrt(sum(x*x for x in v));return tuple(x/l for x in v) if l else (0.,0.,1.)
for d in A:
 draw=d['draw'];idx=draw['index']
 if idx not in matches:continue
 match=matches[idx];v=d['vertex_buffers'];ib=d['index_buffer'];stride=v['pStrides'][0];assert stride==48
 vb=(R/'resources'/f"buffer-{v['pBuffers'][0]}.bin").read_bytes();b=(R/'resources'/f"buffer-{ib['buffer']}.bin").read_bytes();assert ib['indexType']=='VK_INDEX_TYPE_UINT16'
 args=draw['args'];n=args['indexCount'];io=ib['offset']+args['firstIndex']*2;inds=struct.unpack_from('<%dH'%n,b,io);inds=[x+args['vertexOffset'] for x in inds];used=sorted(set(inds));remap={x:i for i,x in enumerate(used)};dyn=next(u['float_values'] for u in draw['uniforms'] if u['binding']==4);world=dyn[:16];vectors=dyn[16:32];verts=[]
 for old in used:
  off=v['pOffsets'][0]+old*stride;pos=struct.unpack_from('<3f',vb,off);uv=struct.unpack_from('<2f',vb,off+12);frame=[]
  for no in [20,28,36]:
   local=[max(x/32767.,-1.) for x in struct.unpack_from('<3h',vb,off+no)];frame.extend(norm(transform(local,vectors,False)))
  color=tuple(x/255. for x in vb[off+44:off+48]);verts.append((*transform(pos,world,True),*uv,*frame,*color))
 assert all(len(z)==18 and all(math.isfinite(x) for x in z) for z in verts)
 header=struct.pack('<4s7I',b'OAWM',1,match['material'],match['reflection_image'],len(verts),len(inds),72,idx);body=b''.join(struct.pack('<18f',*z) for z in verts)+struct.pack('<%dI'%len(inds),*[remap[x] for x in inds]);raw=header+body;fn=f'water-draw-{idx}.oawm';(O/fn).write_bytes(raw)
 bounds=[[min(x[k] for x in verts) for k in range(3)],[max(x[k] for x in verts) for k in range(3)]]
 manifest.append(dict(draw=idx,phase=108,material=match['material'],reflection_image=match['reflection_image'],file=fn,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),vertices=len(verts),indices=len(inds),bounds=bounds,source_vertex_buffer=v['pBuffers'][0],source_index_buffer=ib['buffer'],world_matrix=world,world_vector_matrix=vectors,global_tint=dyn[52:56],luminance_factors=dyn[56:60],luminance_tint=dyn[60:63],vertex_red_range=[min(x[14] for x in verts),max(x[14] for x in verts)]))
meta=dict(format='little endian header <4s7I: OAWM,version1,materialId,reflectionImage,vertexCount,indexCount,stride72,originalDrawIndex; vertex float18 position3,uv2,normal3,tangent3,binormal3,color4; index u32',world_convention='native world coordinates, z up; normal/worldVector native transformed and individually normalized; no WVP/camera data baked',index_winding='native triangle order retained; captured clockwise-front backface cull; GLES clip-conversion may require existing renderer winding policy',draws=manifest)
(R/'water-mesh-manifest.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))
