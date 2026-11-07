from pathlib import Path
import collections,json,struct
Q=Path(__file__).resolve().parent;R=Q.parent;C=R.parent/'open-amalur-native-camera'
matches=json.loads((Q/'captured-image-matches.json').read_text());wanted={r['image']:sorted({h['texture']for h in r['source_matches']})for r in matches}
idx=json.loads((C/'capture-index.json').read_text());draws={d['index']:d for d in idx['draws']};ps=json.loads((C/'pipeline-index.json').read_text())
def pairs(module):
 b=(C/'shaders'/f'module-{module}.spv').read_bytes();w=struct.unpack('<%dI'%(len(b)//4),b);o=5;binding={};loaded={};samples=[]
 while o<len(w):
  n=w[o]>>16;op=w[o]&65535;a=w[o+1:o+n]
  if op==71 and len(a)>=3 and a[1]==33:binding[a[0]]=a[2]
  if op==61:loaded[a[1]]=a[2]
  if op==86:samples.append((a[2],a[3]))
  o+=n
 return [(binding[loaded[im]],binding[loaded[sm]])for im,sm in samples]
pipeline_pairs={int(pid):pairs(next(s['module']for s in p['pStages']if s['stage']=='VK_SHADER_STAGE_FRAGMENT_BIT'))for pid,p in ps.items()if any(s['stage']=='VK_SHADER_STAGE_FRAGMENT_BIT'for s in p['pStages'])}
views={};samplers={};sets={};bound={};result=collections.defaultdict(list)
for line in (R/'evidence/dalentarth.jsonl').open():
 try:r=json.loads(line)
 except json.JSONDecodeError:continue
 f=r.get('vkFunc',{});n=f.get('name');a=f.get('args',{});i=r.get('index')
 if n=='vkCreateImageView':views[a['pView']]=a['pCreateInfo']
 elif n=='vkCreateSampler':samplers[a['pSampler']]=a['pCreateInfo']
 elif n=='vkUpdateDescriptorSets':
  for v in a['pDescriptorWrites']:sets.setdefault(v['dstSet'],{})[v['dstBinding']]=v
 elif n=='vkCmdBindDescriptorSets':bound[a['commandBuffer']]=a
 if i in draws and a['commandBuffer']in bound:
  d=draws[i];ds=sets[bound[a['commandBuffer']]['pDescriptorSets'][0]]
  for imbind,smbind in pipeline_pairs.get(d['pipeline'],[]):
   for im in ds.get(imbind,{}).get('pImageInfo')or[]:
    view=views.get(im['imageView']);image=view['image']if view else None
    if image not in wanted:continue
    infos=ds[smbind]['pImageInfo'];assert len(infos)==1;sid=infos[0]['sampler'];state=samplers[sid]
    result[image].append(dict(draw=i,phase=d['phase'],pipeline=d['pipeline'],image_binding=imbind,sampler_binding=smbind,view=im['imageView'],sampler=sid,state=state))
rows=[]
for image,ids in wanted.items():
 records=result[image];assert records;states=collections.defaultdict(list)
 for r in records:states[json.dumps(r['state'],sort_keys=True)].append({k:v for k,v in r.items()if k!='state'})
 rows.append(dict(texture_ids=ids,image=image,variants=[dict(state=json.loads(s),uses=u)for s,u in states.items()]))
(Q/'captured-sampler-contracts.json').write_text(json.dumps(rows,indent=2))
for r in rows:
 print('texture',r['texture_ids'],'image',r['image'])
 for v in r['variants']:
  s=v['state'];print('uses',len(v['uses']),'samplers',sorted(set(u['sampler']for u in v['uses'])),'state',{k:s[k]for k in ['magFilter','minFilter','mipmapMode','addressModeU','addressModeV','addressModeW','anisotropyEnable','maxAnisotropy','mipLodBias','minLod','maxLod']})
