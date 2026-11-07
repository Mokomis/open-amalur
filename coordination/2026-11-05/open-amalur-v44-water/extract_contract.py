from pathlib import Path
import json,struct,hashlib,collections
ROOT=Path(__file__).resolve().parent; S=ROOT.parent/'open-amalur-native-camera'; E=ROOT/'evidence'
I=json.loads((S/'capture-index.json').read_text()); P=json.loads((S/'pipeline-index.json').read_text());M=(S/'memory-52.bin').read_bytes()
records=[]
for l in (E/'dalentarth.jsonl').open():
 try:records.append(json.loads(l))
 except json.JSONDecodeError:pass
T={d['index']:d for d in I['draws'] if d['phase'] in [108,109] or (d['phase']==111 and d['pipeline'] in [12393,12391])}
sets={};images={};views={};samplers={};bindings={};vertex={};ib={};ans=[]
for rec in records:
 f=rec.get('vkFunc',{});n=f.get('name');a=f.get('args',{});idx=rec.get('index')
 if n=='vkCreateImage':images[a['pImage']]=a['pCreateInfo']
 elif n=='vkCreateImageView':views[a['pView']]=a['pCreateInfo']
 elif n=='vkCreateSampler':samplers[a['pSampler']]=a['pCreateInfo']
 elif n=='vkUpdateDescriptorSets':
  for w in a['pDescriptorWrites']:sets.setdefault(w['dstSet'],{})[w['dstBinding']]=dict(index=idx,**w)
 elif n=='vkCmdBindDescriptorSets':bindings[a['commandBuffer']]=a
 elif n and n.startswith('vkCmdBindVertexBuffers'):vertex[a['commandBuffer']]=a
 elif n=='vkCmdBindIndexBuffer':ib[a['commandBuffer']]=a
 if idx in T:
  d=T[idx];b=bindings[a['commandBuffer']];des=sets[b['pDescriptorSets'][0]];entry=dict(draw=d,bind=b,index_buffer=ib.get(a['commandBuffer']),vertex_buffers=vertex.get(a['commandBuffer']),descriptors={})
  for k,v in sorted(des.items()):
   q=dict(v)
   for im in q.get('pImageInfo') or []:
    if im['imageView'] in views:
     q['view']=views[im['imageView']];q['image']=images[q['view']['image']]
    if im['sampler'] in samplers:q['sampler']=samplers[im['sampler']]
   entry['descriptors'][k]=q
  for u in d['uniforms']:
   if u['memory']==52:
    size=min(u['range'],1376);raw=M[u['offset']:u['offset']+size];u['float_values']=struct.unpack('<%df'%(size//4),raw)
    if u['binding']==0:(E/f'material-draw-{idx}.bin').write_bytes(raw[:96])
  ans.append(entry)
(ROOT/'active-water-bindings.json').write_text(json.dumps(ans,indent=2));(ROOT/'water-pipelines.json').write_text(json.dumps({str(k):P[str(k)] for k in {d['pipeline'] for d in T.values()}},indent=2))
print('captured draws',len(ans))
