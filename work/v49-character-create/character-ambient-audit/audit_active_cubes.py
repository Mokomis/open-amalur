"""Read existing JSONL only; preserve exact active cube descriptors by draw."""
from pathlib import Path
import json,collections
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
OUT=ROOT/'work/v49-character-create/character-ambient-audit'
images={};views={};samplers={};sets={};pipes={};state={};phase=0;rows=[];phaseinfo={};writes=[]
for ln,l in enumerate((ROOT/'work/v33-native-camera/dalentarth.jsonl').open()):
 if ln==0 or not l.strip():continue
 j=json.loads(l);f=j.get('vkFunc',{});n=f.get('name','');a=f.get('args',{});idx=j.get('index')
 if n=='vkCreateImage':images[a['pImage']]=a['pCreateInfo']
 elif n=='vkCreateImageView':views[a['pView']]=a['pCreateInfo']
 elif n=='vkCreateSampler':samplers[a['pSampler']]=a['pCreateInfo']
 elif n=='vkCreateGraphicsPipelines':
  infos=a['pCreateInfos'];handles=a['pPipelines']
  for h,ci in zip(handles,infos):pipes[h]=ci
 elif n=='vkUpdateDescriptorSets':
  for w in a.get('pDescriptorWrites') or []:
   count=w['descriptorCount'];start=w.get('dstArrayElement',0)
   for k in range(count):
    entry={'descriptorType':w['descriptorType']}
    if w.get('pImageInfo'):entry['image']=w['pImageInfo'][k]
    if w.get('pBufferInfo'):entry['buffer']=w['pBufferInfo'][k]
    sets.setdefault(w['dstSet'],{})[(w['dstBinding'],start+k)]=entry
  for cp in a.get('pDescriptorCopies') or []:
   for k in range(cp['descriptorCount']):
    src=sets[cp['srcSet']][(cp['srcBinding'],cp.get('srcArrayElement',0)+k)]
    sets.setdefault(cp['dstSet'],{})[(cp['dstBinding'],cp.get('dstArrayElement',0)+k)]=dict(src)
 elif n=='vkBeginCommandBuffer':state[a['commandBuffer']]={}
 elif n=='vkCmdBeginRendering':
  phase+=1;state.setdefault(a['commandBuffer'],{})['phase']=phase
  phaseinfo[phase]={'index':idx,'rendering':a['pRenderingInfo']}
 elif n=='vkCmdBindPipeline':state.setdefault(a['commandBuffer'],{})['pipeline']=a['pipeline']
 elif n=='vkCmdBindDescriptorSets':
  s=state.setdefault(a['commandBuffer'],{});bound=s.setdefault('sets',{})
  for k,h in enumerate(a['pDescriptorSets']):bound[a['firstSet']+k]=h
 elif n in ['vkCmdDraw','vkCmdDrawIndexed']:
  s=state[a['commandBuffer']];ph=s.get('phase');pi=s.get('pipeline');cube=[];samp=[]
  for setslot,h in sorted(s.get('sets',{}).items()):
   for (slot,elem),w in sorted(sets.get(h,{}).items()):
    im=w.get('image',{});v=views.get(im.get('imageView'),{})
    if im.get('sampler'):samp.append({'set_slot':setslot,'set':h,'binding':slot,'array_element':elem,'sampler':im['sampler'],'sampler_info':samplers[im['sampler']]})
    if v.get('viewType') in ['VK_IMAGE_VIEW_TYPE_CUBE','VK_IMAGE_VIEW_TYPE_CUBE_ARRAY']:
     ci=images[v['image']]
     cube.append({'set_slot':setslot,'set':h,'binding':slot,'array_element':elem,**im,'image':v['image'],'view_info':v,'image_info':ci})
  if cube and ph in [93,97,98,108,109,111]:
   pipe=pipes.get(pi,{});rows.append({'index':idx,'phase':ph,'pipeline':pi,'stages':pipe.get('pStages'),'cube_bindings':cube,'sampler_bindings':samp})
(OUT/'active-cube-draws.json').write_text(json.dumps(rows,indent=2))
(OUT/'capture-resources.json').write_text(json.dumps({'images':images,'views':views,'samplers':samplers,'phases':{k:phaseinfo[k] for k in [97,98,108,109,111]}},indent=2))
count=collections.Counter((x['phase'],tuple((s['stage'],s['module']) for s in x['stages']),tuple((c['binding'],c['image']) for c in x['cube_bindings'])) for x in rows)

print('rows',len(rows))
