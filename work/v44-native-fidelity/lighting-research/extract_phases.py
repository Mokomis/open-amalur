from pathlib import Path
import json,struct,subprocess,shutil
root=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera');out=Path('/private/tmp/oa-v44-lighting')
idx=json.loads((root/'capture-index.json').read_text());pipes=json.loads((root/'pipeline-index.json').read_text());mem=(root/'memory-52.bin').read_bytes()
sets={};images={};views={};samplers={};state={};passes=[];phase=0
for ln,l in enumerate(open('/private/tmp/oa-dalentarth.jsonl')):
 if ln==0:continue
 j=json.loads(l);i=j['index'];f=j.get('vkFunc',{});n=f.get('name','');a=f.get('args',{})
 if n=='vkCreateImage':images[a['pImage']]=a['pCreateInfo']
 if n=='vkCreateImageView':views[a['pView']]=a['pCreateInfo']
 if n=='vkCreateSampler':samplers[a['pSampler']]=a['pCreateInfo']
 if n=='vkUpdateDescriptorSets':
  for w in a.get('pDescriptorWrites') or []:sets.setdefault(w['dstSet'],{})[w['dstBinding']]=w
 if n=='vkBeginCommandBuffer':state[a['commandBuffer']]={}
 if n=='vkCmdBeginRendering':
  phase+=1;state.setdefault(a['commandBuffer'],{})['phase']=phase
  passes.append(dict(index=i,phase=phase,rendering=a['pRenderingInfo'],draws=[]))
 if n=='vkCmdBindPipeline':state.setdefault(a['commandBuffer'],{})['pipeline']=a['pipeline']
 if n=='vkCmdBindDescriptorSets':state.setdefault(a['commandBuffer'],{})['descriptors']=a
 if n in ('vkCmdDraw','vkCmdDrawIndexed'):
  s=state[a['commandBuffer']];ph=s.get('phase',0)
  if ph<93 or ph>136:continue
  p=pipes[str(s['pipeline'])];b=s['descriptors'];d=dict(index=i,pipeline=s['pipeline'],modules=[x['module'] for x in p['pStages']],bind=b,descriptors=json.loads(json.dumps({str(sid):sets[sid] for sid in b['pDescriptorSets']})),uniforms=[],sampled=[])
  dyn=iter(b.get('pDynamicOffsets') or [])
  for sid in b['pDescriptorSets']:
   for slot,w in sorted(sets[sid].items()):
    for ub in w.get('pBufferInfo') or []:
     off=ub['offset']+(next(dyn) if 'DYNAMIC' in w['descriptorType'] else 0)
     d['uniforms'].append(dict(slot=slot,offset=off,size=ub['range'],values=struct.unpack('<%df'%(ub['range']//4),mem[off:off+ub['range']]) if ub['buffer']==51 else None))
    for im in w.get('pImageInfo') or []:
     if im['imageView']:
      v=views[im['imageView']];imdata=images[v['image']];d['sampled'].append(dict(slot=slot,view=im['imageView'],image=v['image'],format=v['format'],extent=imdata['extent']))
  passes[-1]['draws'].append(d)
selected=[p for p in passes if 93<=p['phase']<=136]
for p in selected:
 p['outputs']=[]
 for a in p['rendering']['pColorAttachments'] or []:
  v=views[a['imageView']];p['outputs'].append(dict(view=a['imageView'],image=v['image'],format=v['format'],extent=images[v['image']]['extent']))
 print('PH',p['phase'],'out',[(x['view'],x['extent'],x['format']) for x in p['outputs']])
 for d in p['draws']: print(' ',d['index'],d['pipeline'],d['modules'],'in',[(x['slot'],x['view']) for x in d['sampled']])
 for d in p['draws']:
  for m in d['modules']:
   sf=Path(idx['shaders'][str(m)]['path']);shutil.copyfile(sf,out/sf.name);subprocess.run(['spirv-dis',str(sf),'-o',str(out/(sf.stem+'.spvasm'))],check=True)
(out/'phases.json').write_text(json.dumps(selected,indent=2));(out/'resources.json').write_text(json.dumps(dict(images=images,views=views,samplers=samplers),indent=2))
