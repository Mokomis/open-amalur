from pathlib import Path
import json,collections
Q=Path(__file__).resolve().parent;C=Q.parent.parent/'2026-11-05/open-amalur-native-camera';R=Q.parent.parent/'2026-11-05/open-amalur-v44-water'
I=json.loads((C/'capture-index.json').read_text());P=json.loads((C/'pipeline-index.json').read_text())
targets={69912:'main-G0-G1-G2',66881:'AO-generation-complete',66891:'AO-bilateral-horizontal-complete',66901:'AO-bilateral-vertical-complete',71740:'shadow-cascade0',72264:'shadow-cascade1',72641:'shadow-cascade2',72932:'deferred-combine',72940:'scene-plus-sky',72984:'scene-before-fog-water-complete',73026:'scene-after-fog',73214:'scene-after-transparents',73395:'generated-color-LUT',73404:'post-LUT-bloom-merge',73411:'final-AA-before-HUD'}
images={};views={};begins={};active_render={};render_ranges={};events={};submits={};sets={};bound={}
for line in (R/'evidence/dalentarth.jsonl').open():
 try:r=json.loads(line)
 except json.JSONDecodeError:continue
 f=r.get('vkFunc',{});n=f.get('name');a=f.get('args',{});i=r.get('index');cb=a.get('commandBuffer')
 if n=='vkCreateImage':images[a['pImage']]=a['pCreateInfo']
 elif n=='vkCreateImageView':views[a['pView']]=a['pCreateInfo']
 elif n=='vkBeginCommandBuffer':begins[cb]=i
 elif n and n.startswith('vkCmdBeginRendering'):active_render[cb]=(i,a)
 elif n and n.startswith('vkCmdEndRendering'):
  start,info=active_render.pop(cb);render_ranges[start]=[start,i]
 elif n=='vkUpdateDescriptorSets':
  for w in a['pDescriptorWrites']:sets.setdefault(w['dstSet'],{})[w['dstBinding']]=w
 elif n=='vkCmdBindDescriptorSets':bound[cb]=a
 elif n=='vkQueueSubmit':
  for s in a['pSubmits']:
   for c in s['pCommandBuffers']:submits[(c,begins[c])]=i
 if i in targets:
  bind=bound[cb];descriptors={}
  for k,v in sets[bind['pDescriptorSets'][0]].items():
   for im in v.get('pImageInfo')or[]:
    if im['imageView']in views:descriptors[k]=dict(view=im['imageView'],image=views[im['imageView']]['image'])
  events[i]=dict(name=targets[i],command_buffer=cb,begin_command_buffer=begins[cb],render_begin=active_render[cb][0],descriptors=descriptors)
byphase={p['index']:p for p in I['passes']};draws={d['index']:d for d in I['draws']};bpp={'VK_FORMAT_R8G8B8A8_UNORM':4,'VK_FORMAT_B8G8R8A8_UNORM':4,'VK_FORMAT_R16G16B16A16_SFLOAT':8,'VK_FORMAT_A2R10G10B10_UNORM_PACK32':4,'VK_FORMAT_A2B10G10R10_UNORM_PACK32':4,'VK_FORMAT_D24_UNORM_S8_UINT':4,'VK_FORMAT_D16_UNORM':2,'VK_FORMAT_D32_SFLOAT':4,'VK_FORMAT_R32_SFLOAT':4}
for i,e in events.items():
 e['queue_submit']=submits[(e['command_buffer'],e['begin_command_buffer'])];e['render_range']=render_ranges[e['render_begin']];info=byphase[e['render_begin']]['info'];e['phase']=byphase[e['render_begin']]['phase'];d=draws[i];e['pipeline']=d['pipeline'];e['fragment_module']=next(s['module']for s in P[str(d['pipeline'])]['pStages']if s['stage']=='VK_SHADER_STAGE_FRAGMENT_BIT');e['attachments']=[]
 for role,items in [('color',info.get('pColorAttachments')or[]),('depth',[info['pDepthAttachment']]if info.get('pDepthAttachment')else[])]:
  for k,a in enumerate(items):
   v=views[a['imageView']];ci=images[v['image']];w,h=ci['extent']['width'],ci['extent']['height'];fmt=ci['format'];e['attachments'].append(dict(role=role,index=k,view=a['imageView'],image=v['image'],format=fmt,width=w,height=h,raw_estimated_bytes=w*h*bpp.get(fmt,4)))
configs={}
for name,ids,depth in [('gbuffer',[69912],True),('shadows',[71740,72264,72641],True),('stages',[66881,66891,66901,72932,72940,72984,73026,73214,73395,73404,73411],False),('all-selected',sorted(targets),True)]:
 groups=collections.defaultdict(list)
 for i in ids:groups[(events[i]['begin_command_buffer'],events[i]['queue_submit'])].append(i)
 cfg=dict(DumpResourcesOptions=dict(Scale=1.0,ImageFormat='png',DumpBeforeCommand=False,DumpDepth=depth,DumpVertexIndexBuffer=False,DumpAllDescriptors=False,DumpAllImageSubresources=False,DumpRawImages=True,DumpSeparateAlpha=False,JsonOutputPerCommand=True,BinaryFileCompressionType='none'),BeginCommandBuffer=[],Draw=[],RenderPass=[],QueueSubmit=[])
 total=0
 for(begin,submit),di in sorted(groups.items()):
  cfg['BeginCommandBuffer'].append(begin);cfg['QueueSubmit'].append(submit);cfg['Draw'].append(sorted(di));cfg['RenderPass'].append(sorted({tuple(events[i]['render_range'])for i in di}))
  total+=sum(a['raw_estimated_bytes']for i in di for a in events[i]['attachments']if a['role']=='color'or depth)
 (Q/f'dump-{name}.json').write_text(json.dumps(cfg,indent=2));configs[name]=dict(draws=ids,estimated_raw_attachment_bytes=total)
result=dict(capture_sha256='72c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209',events={str(i):e for i,e in sorted(events.items())},configs=configs,estimated_three_category_raw_attachment_bytes=sum(c['estimated_raw_attachment_bytes']for k,c in configs.items()if k!='all-selected'),estimated_single_replay_raw_attachment_bytes=configs['all-selected']['estimated_raw_attachment_bytes'],index_contract='Capture JSONL index / capture-index draws[index] is the Vulkan dump block index. Phase is analysis-only. New source additionally supports an automatic submit/command/draw tuple preprocessing mode, but this plan explicitly uses verified Vulkan block indices in JSON.')
(Q/'dump-stage-plan.json').write_text(json.dumps(result,indent=2))
print(json.dumps(configs,indent=2));print('single-replay bytes',result['estimated_single_replay_raw_attachment_bytes'])
for i,e in sorted(events.items()):print(i,e['name'],e['render_range'],e['begin_command_buffer'],e['queue_submit'],e['attachments'])
