"""Read retained capture JSONL and memory only for one already identified mountain pose."""
from pathlib import Path
import json,struct
Q=Path(__file__).resolve().parent;C=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera');mem=(C/'memory-52.bin').read_bytes();pipes=json.loads((C/'pipeline-index.json').read_text())
sets={};layouts={};views={};samplers={};states={};rows=[]
with open('/private/tmp/oa-dalentarth.jsonl') as f:
 for line in f:
  try:r=json.loads(line)
  except:continue
  fn=r.get('vkFunc',{});name=fn.get('name');a=fn.get('args',{})
  if name=='vkCreateDescriptorSetLayout':layouts[a['pSetLayout']]=a['pCreateInfo']
  elif name=='vkAllocateDescriptorSets':
   for ds,layout in zip(a['pDescriptorSets'],a['pAllocateInfo']['pSetLayouts']):sets[ds]={'layout':layout,'bindings':{}}
  elif name=='vkUpdateDescriptorSets':
   for w in a.get('pDescriptorWrites') or []:sets[w['dstSet']]['bindings'][w['dstBinding']]=w
  elif name=='vkCreateImageView':views[a['pView']]=a['pCreateInfo']
  elif name=='vkCreateSampler':samplers[a['pSampler']]=a['pCreateInfo']
  elif name in ['vkCmdBindVertexBuffers','vkCmdBindVertexBuffers2','vkCmdBindVertexBuffers2EXT']:
   s=states.setdefault(a['commandBuffer'],{});s['vertex']=a
  elif name=='vkCmdBindIndexBuffer':states.setdefault(a['commandBuffer'],{})['index']=a
  elif name=='vkCmdBindPipeline':states.setdefault(a['commandBuffer'],{})['pipeline']=a['pipeline']
  elif name=='vkCmdBindDescriptorSets':states.setdefault(a['commandBuffer'],{})['descriptor']=a
  elif name=='vkCmdDrawIndexed':
   s=states[a['commandBuffer']]
   if (s.get('vertex',{}).get('pBuffers') or [None])[0]!=12224 or s.get('index',{}).get('buffer')!=12226:continue
   bind=s['descriptor'];ds=bind['pDescriptorSets'][0];record=sets[ds];dynamic=[]
   for b in sorted(layouts[record['layout']]['pBindings'],key=lambda b:b['binding']):
    if 'DYNAMIC' in b['descriptorType']:dynamic.extend([b['binding']]*b['descriptorCount'])
   offs=dict(zip(dynamic,bind.get('pDynamicOffsets') or []));bindings=record['bindings'];world=bindings.get(68) or bindings.get(4)
   if world is None:continue
   bi=world['pBufferInfo'][0];off=bi['offset']+offs.get(world['dstBinding'],0);matrix=list(struct.unpack_from('<16f',mem,off))
   if max(abs(x-y) for x,y in zip(matrix[12:15],[-86586.15625,-17710.791015625,8000]))>.01:continue
   images={};uniforms={}
   for k,v in bindings.items():
    if v.get('pImageInfo'):
     infos=v['pImageInfo'];images[str(k)]=dict(info=infos,views=[views.get(i['imageView']) for i in infos],samplers=[samplers.get(i['sampler']) for i in infos])
    if v.get('pBufferInfo'):
     bi=v['pBufferInfo'][0];at=bi['offset']+offs.get(k,0);n=min(bi['range'],256);uniforms[str(k)]=dict(info=bi,dynamic_offset=offs.get(k,0),absolute_offset=at,float_values=list(struct.unpack_from('<'+str(n//4)+'f',mem,at)))
   pi=pipes.get(str(s['pipeline']),{});rows.append(dict(draw=r['index'],pipeline=s['pipeline'],stages=pi.get('pStages'),raster=pi.get('pRasterizationState'),depth=pi.get('pDepthStencilState'),descriptor_set=ds,world_matrix=matrix,images=images,uniforms=uniforms,args=a))
(Q/'mountain-2061-native-bindings.json').write_text(json.dumps(rows,indent=2));print([(r['draw'],[(s['stage'],s['module']) for s in r['stages']],r['descriptor_set'],r['images'].keys()) for r in rows])
