from pathlib import Path
import json,copy
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur');OUT=ROOT/'work/v49-character-create/skin-colour-contract-audit'
images={};views={};sets={};state={};vertices={};indices={};layouts={};phase=0;result={}
for ln,l in enumerate((ROOT/'work/v33-native-camera/dalentarth.jsonl').open()):
 if not ln or not l.strip():continue
 j=json.loads(l);f=j.get('vkFunc',{});n=f.get('name','');a=f.get('args',{});idx=j.get('index')
 if n=='vkCreateImage':images[a['pImage']]=a['pCreateInfo']
 elif n=='vkCreateImageView':views[a['pView']]=a['pCreateInfo']
 elif n=='vkCreateDescriptorSetLayout':layouts[a['pSetLayout']]=a['pCreateInfo']
 elif n=='vkUpdateDescriptorSets':
  for w in a.get('pDescriptorWrites') or []:
   for k in range(w['descriptorCount']):
    e={'descriptorType':w['descriptorType'],'last_write_event':idx}
    if w.get('pImageInfo'):e['image']=w['pImageInfo'][k]
    if w.get('pBufferInfo'):e['buffer']=w['pBufferInfo'][k]
    sets.setdefault(w['dstSet'],{})[(w['dstBinding'],w.get('dstArrayElement',0)+k)]=e
  for c in a.get('pDescriptorCopies') or []:
   for k in range(c['descriptorCount']):
    sets.setdefault(c['dstSet'],{})[(c['dstBinding'],c.get('dstArrayElement',0)+k)]=copy.deepcopy(sets[c['srcSet']][(c['srcBinding'],c.get('srcArrayElement',0)+k)])
 elif n=='vkBeginCommandBuffer':state[a['commandBuffer']]={}
 elif n=='vkCmdBindVertexBuffers2':vertices[a['commandBuffer']]={'event':idx,'args':a}
 elif n=='vkCmdBindIndexBuffer':indices[a['commandBuffer']]={'event':idx,'args':a}
 elif n=='vkCmdBindDescriptorSets':
  s=state.setdefault(a['commandBuffer'],{})
  for k,h in enumerate(a['pDescriptorSets']):s[a['firstSet']+k]={'set':h,'last_bind_event':idx,'bind_args':a}
 elif n in ['vkCmdDraw','vkCmdDrawIndexed'] and idx in {67663,67691}:
  for slot,b in state[a['commandBuffer']].items():
   entries=[]
   for (binding,el),e in sorted(sets[b['set']].items()):
    e=copy.deepcopy(e)
    if 'image' in e and e['image'].get('imageView'):
     v=views[e['image']['imageView']];e['view_info']=v;e['image_info']=images[v['image']]
    entries.append({'binding':binding,'array_element':el,**e})
   result[str(slot)]={**b,'entries':entries}
  out={'draw':idx,'draw_args':a,'bound_sets':result,'vertex_binding':vertices.get(a['commandBuffer']),'index_binding':indices.get(a['commandBuffer'])}
  (OUT/f'draw-{idx}-bindings.json').write_text(json.dumps(out,indent=2)+'\n')
  discarded=(json.dumps({'binds':[{k:v for k,v in b.items() if k!='entries'} for b in result.values()],'images':[{'binding':e['binding'],'view':e.get('image',{}).get('imageView'),'image':e.get('view_info',{}).get('image'),'format':e.get('image_info',{}).get('format'),'extent':e.get('image_info',{}).get('extent'),'mips':e.get('image_info',{}).get('mipLevels')} for b in result.values() for e in b['entries'] if 'view_info' in e],'uniforms':[e for b in result.values() for e in b['entries'] if 'buffer' in e]}))
  if idx==67691:break
