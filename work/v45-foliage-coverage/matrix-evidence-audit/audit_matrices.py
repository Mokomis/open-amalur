import json,struct,ctypes,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
C=Path('/private/tmp/oa-dalentarth-20261105.gfxr')
J=Path('/private/tmp/oa-dalentarth.jsonl')
N=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera')
TARGETS={68811,69284};sets={};layouts={};setlayouts={};pipes={};bufmem={};state={};draws={};raw=[];lastwrites={};submit=[];writers=[];memevents=[]
for number,line in enumerate(J.open()):
 if number==0:continue
 r=json.loads(line);i=r['index'];f=r.get('vkFunc',{});name=f.get('name');a=f.get('args',{})
 if name=='vkCreateDescriptorSetLayout':layouts[a['pSetLayout']]=a['pCreateInfo']
 if name=='vkAllocateDescriptorSets':
  for sid,lay in zip(a['pDescriptorSets'],a['pAllocateInfo']['pSetLayouts']):setlayouts[sid]=lay
 if name=='vkCreateGraphicsPipelines':
  for h,info in zip(a['pPipelines'],a['pCreateInfos']):pipes[h]=info
 if name=='vkBindBufferMemory':bufmem[a['buffer']]=(a['memory'],a['memoryOffset'])
 if name=='vkUpdateDescriptorSets':
  for w in a.get('pDescriptorWrites') or []:sets.setdefault(w['dstSet'],{})[w['dstBinding']]=w;lastwrites[w['dstSet']]=i
 if name=='vkBeginCommandBuffer':state[a['commandBuffer']]={}
 if name=='vkCmdBindPipeline':state[a['commandBuffer']]['pipeline']=a['pipeline']
 if name=='vkCmdBindDescriptorSets':state[a['commandBuffer']]['descriptor']=r
 if name=='vkCmdBindVertexBuffers2':state[a['commandBuffer']]['vertex']=r
 if name=='vkCmdBindIndexBuffer':state[a['commandBuffer']]['index']=r
 if i in TARGETS:
  s=state[a['commandBuffer']];b=s['descriptor']['vkFunc']['args'];assert b['firstSet']==0 and b['descriptorSetCount']==1
  sid=b['pDescriptorSets'][0];order=sorted(w['binding'] for w in layouts[setlayouts[sid]]['pBindings'] if w['descriptorType'].endswith('_DYNAMIC'))
  assert len(order)==b['dynamicOffsetCount']==len(b['pDynamicOffsets'])
  u=[]
  for slot,dynamic in zip(order,b['pDynamicOffsets']):
   w=sets[sid][slot];assert w['descriptorCount']==1 and w['descriptorType']=='VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER_DYNAMIC'
   info=w['pBufferInfo'][0];mem,base=bufmem[info['buffer']]
   u.append(dict(binding=slot,buffer=info['buffer'],memory=mem,offset=base+info['offset']+dynamic,range=info['range']))
  draws[i]=dict(index=i,args=a,pipeline=s['pipeline'],vs=next(q['module'] for q in pipes[s['pipeline']]['pStages'] if q['stage']=='VK_SHADER_STAGE_VERTEX_BIT'),descriptor_bind=s['descriptor'],set=sid,layout=setlayouts[sid],dynamic_binding_order=order,uniforms=u,last_descriptor_write=lastwrites[sid],vertex=s['vertex'],index_bind=s['index'])
 if (name in ['vkCmdCopyBuffer','vkCmdUpdateBuffer','vkCmdFillBuffer','vkCmdCopyImageToBuffer'] and a.get('dstBuffer')==51):writers.append(r)
 if name in ['vkMapMemory','vkUnmapMemory','vkFlushMappedMemoryRanges','vkInvalidateMappedMemoryRanges'] and (a.get('memory')==52 or any(v.get('memory')==52 for v in a.get('pMemoryRanges',[]) or [])):memevents.append(r)
 if name=='vkQueueSubmit' and any(46 in q.get('pCommandBuffers',[]) for q in a['pSubmits']):submit.append(r)
 if i in TARGETS or 68808<=i<=68811 or 69281<=i<=69284 or i==73630:raw.append(r)
lib=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib');fn=lib.LZ4_decompress_safe;fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int
fills=[];memory=None
with C.open('rb') as f:
 _,_,_,opts=struct.unpack('<4sIII',f.read(16));f.seek(opts*8,1);block=-1
 while True:
  h=f.read(12)
  if not h:break
  size,kind=struct.unpack('<QI',h);block+=1;off=f.tell();d=f.read(size)
  if kind&0x7fffffff==3 and len(d)>=36 and struct.unpack_from('<I',d)[0]&0xffff==2:
   thread,mem,addr,n=struct.unpack_from('<QQQQ',d,4)
   if mem!=52:continue
   if kind&0x80000000:
    out=ctypes.create_string_buffer(n);assert fn(d[36:],out,len(d)-36,n)==n;payload=out.raw
   else:payload=d[36:];assert len(payload)==n
   fills.append(dict(block=block,file_offset=off,stored_size=size,memory=mem,offset=addr,size=n,compressed=bool(kind&0x80000000),sha256=hashlib.sha256(payload).hexdigest()))
   assert addr==0;memory=payload
assert len(fills)==1 and memory is not None
assert fills[0]['block']==73631 and submit[0]['index']==76331
assert memory==N.joinpath('memory-52.bin').read_bytes()
exported={d['index']:d for d in json.loads(P.joinpath('native-gbuffer-draws.json').read_text())}
for i,d in draws.items():
 assert d['uniforms']==exported[i]['uniforms']
 u=next(q for q in d['uniforms'] if q['binding']==68);data=memory[u['offset']:u['offset']+u['range']];P.joinpath('draw-%d-binding68.bin'%i).write_bytes(data)
 d['world_matrix_row_major']=list(struct.unpack_from('<16f',data));d['world_view_projection_row_major']=list(struct.unpack_from('<16f',data,128));d['matrix_export_bit_exact']=struct.pack('<16f',*exported[i]['world_matrix_row_major'])==data[:64]
 assert d['matrix_export_bit_exact']
 d['ubo_slice_sha256']=hashlib.sha256(data).hexdigest()
 d['args_bit_exact']=d['args']==exported[i]['args'];assert d['args_bit_exact']
 for k in ['instanceCount','firstInstance','firstIndex','vertexOffset']:assert d['args'][k]==(1 if k=='instanceCount' else 0)
result=dict(recording=str(C),recording_sha256=hashlib.sha256(C.read_bytes()).hexdigest(),fills52=fills,mapped_memory_events=memevents,submission=submit,gpu_writes_to_buffer51=writers,draws=list(draws.values()),raw_draw_events=raw)
def inv(a):
 a=[list(map(float,row))+[float(i==k) for k in range(4)] for i,row in enumerate(a)]
 for k in range(4):
  z=max(range(k,4),key=lambda i:abs(a[i][k]));a[k],a[z]=a[z],a[k];v=a[k][k];a[k]=[x/v for x in a[k]]
  for i in range(4):
   if i==k:continue
   v=a[i][k];a[i]=[x-v*y for x,y in zip(a[i],a[k])]
 return [row[4:] for row in a]
def mat(a):return [a[k:k+4] for k in range(0,16,4)]
def mul(a,b):return [[sum(a[i][k]*b[k][z] for k in range(4)) for z in range(4)] for i in range(4)]
for d in result['draws']:d['camera_vp_reconstructed_row_major']=sum(mul(inv(mat(d['world_matrix_row_major'])),mat(d['world_view_projection_row_major'])),[])
a,b=[d['camera_vp_reconstructed_row_major'] for d in result['draws']]
result['two_draw_camera_max_linear_delta']=max(abs(a[k]-b[k]) for k in range(12));result['two_draw_camera_translation_deltas']=[a[k]-b[k] for k in range(12,16)]
P.joinpath('matrix-evidence.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(recording_sha256=result['recording_sha256'],fill52=fills,draws=[dict(index=i,translation=d['world_matrix_row_major'][12:15],bit_exact=d['matrix_export_bit_exact']) for i,d in draws.items()],gpu_writers=len(writers)),indent=2))
