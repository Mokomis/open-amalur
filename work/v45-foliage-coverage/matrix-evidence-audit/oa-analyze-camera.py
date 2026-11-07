import json,struct,ctypes,collections
from pathlib import Path
root=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera');(root/'shaders').mkdir(exist_ok=True)
records={};shaders={};pipes={};sets={};buffers={};bindings={};maps={};draws=[];passes=[];state={};phase=0
for num,l in enumerate(open('/private/tmp/oa-dalentarth.jsonl')):
 if num==0:continue
 j=json.loads(l);i=j['index'];f=j.get('vkFunc',{});n=f.get('name','');a=f.get('args',{});records[i]=j
 if n=='vkCreateShaderModule':shaders[i]=a['pShaderModule']
 if n=='vkCreateGraphicsPipelines':
  for h,v in zip(a['pPipelines'],a['pCreateInfos']):pipes[h]=v
 if n=='vkCreateBuffer':buffers[a['pBuffer']]=a['pCreateInfo']
 if n=='vkBindBufferMemory':bindings[a['buffer']]=(a['memory'],a['memoryOffset'])
 if n=='vkMapMemory':maps[a['memory']]=(a['offset'],a['size'])
 if n=='vkUpdateDescriptorSets':
  for w in a.get('pDescriptorWrites') or []:sets.setdefault(w['dstSet'],{})[w['dstBinding']]=w
 if n=='vkBeginCommandBuffer':state[a['commandBuffer']]={}
 if n=='vkCmdBeginRendering':
  phase+=1;passes.append({'index':i,'phase':phase,'info':a['pRenderingInfo'],'draws':0});state.setdefault(a['commandBuffer'],{})['phase']=phase
 if n=='vkCmdBindPipeline':state.setdefault(a['commandBuffer'],{})['pipeline']=a['pipeline']
 if n=='vkCmdBindDescriptorSets':state.setdefault(a['commandBuffer'],{})['descriptors']=a
 if n in ['vkCmdDraw','vkCmdDrawIndexed']:
  s=state[a['commandBuffer']];p=pipes.get(s.get('pipeline'),{});d=s.get('descriptors',{});dyn=iter(d.get('pDynamicOffsets') or []);ubs=[]
  for sid in d.get('pDescriptorSets') or []:
   for slot,w in sorted(sets.get(sid,{}).items()):
    if 'UNIFORM_BUFFER' in w['descriptorType']:
     for b in w['pBufferInfo']:
      do=next(dyn) if 'DYNAMIC' in w['descriptorType'] else 0;mem,off=bindings[b['buffer']];ubs.append({'binding':slot,'buffer':b['buffer'],'memory':mem,'offset':off+b['offset']+do,'range':b['range']})
  dr={'index':i,'phase':s.get('phase'),'pipeline':s.get('pipeline'),'vs':next((v['module'] for v in p.get('pStages',[]) if v['stage']=='VK_SHADER_STAGE_VERTEX_BIT'),None),'args':a,'uniforms':ubs};draws.append(dr)
  if passes:passes[-1]['draws']+=1
lib=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib');fn=lib.LZ4_decompress_safe;fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int
def dec(src,n):
 out=ctypes.create_string_buffer(n);got=fn(src,out,len(src),n);assert got==n,(got,n);return out.raw
extracted={};fills=[];index=-1
with open('/private/tmp/oa-dalentarth-20261105.gfxr','rb') as f:
 _,_,_,opts=struct.unpack('<4sIII',f.read(16));f.seek(opts*8,1)
 while True:
  h=f.read(12)
  if not h:break
  size,kind=struct.unpack('<QI',h);data=f.read(size);index+=1
  if index in shaders:
   if kind&0x80000000:data=data[:12]+dec(data[20:],struct.unpack_from('<Q',data,12)[0])
   pos=data.find(b'\x03\x02\x23\x07');assert pos>=0,(index,hex(kind));code=data[pos:]
   # pCode's encoded array length bounds source; trim at exact codeSize from JSON.
   length=records[index]['vkFunc']['args']['pCreateInfo']['codeSize'];code=code[:length];assert len(code)==length
   path=root/'shaders'/('module-'+str(shaders[index])+'.spv');path.write_bytes(code);extracted[shaders[index]]={'block':index,'bytes':length,'path':str(path)}
  if kind&0x7fffffff==3 and struct.unpack_from('<I',data)[0]&0xffff==2:
   thread,mem,off,n=struct.unpack_from('<QQQQ',data,4);fills.append({'block':index,'memory':mem,'offset':off,'size':n,'file_offset':f.tell()-size,'stored_size':size,'compressed':bool(kind&0x80000000)})
out={'shaders':extracted,'draws':draws,'passes':passes,'buffers':buffers,'buffer_memory':bindings,'maps':maps,'fills':fills,'pipeline_count':len(pipes),'block_count':index}
(root/'capture-index.json').write_text(json.dumps(out,indent=2)+'\n')
print('shaders',len(extracted),'draws',len(draws),'passes',len(passes),'blocks',index)
print('top vertex shaders',collections.Counter(d['vs'] for d in draws).most_common(12))
print('passes',[(p['phase'],p['index'],p['draws'],len(p['info'].get('pColorAttachments') or []),p['info']['renderArea']['extent']) for p in passes[:14]])
print('first draw',draws[0])
