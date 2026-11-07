from pathlib import Path
import json,collections
Q=Path(__file__).resolve().parent;BASE=Q.parent;C=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera');R=Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-v44-water')
targets={73221:'DOF-input-copy-and-depth',73230:'DOF-quarter-fuzz-downsample',73237:'DOF-quarter-blur-horizontal',73244:'DOF-quarter-blur-vertical',73253:'DOF-half-fuzz',73262:'DOF-full-effect',73271:'post-DOF-half-downsample',73280:'bloom-extraction-quarter',73386:'final-bloom-quarter'}
idx=json.loads((C/'capture-index.json').read_text());pipelines=json.loads((C/'pipeline-index.json').read_text());draws={d['index']:d for d in idx['draws']};phases={p['index']:p for p in idx['passes']}
images={};views={};samplers={};sets={};bound={};begins={};active={};ends={};events={};submits={}
for line in (R/'evidence/dalentarth.jsonl').open():
 try:r=json.loads(line)
 except json.JSONDecodeError:continue
 f=r.get('vkFunc',{});n=f.get('name');a=f.get('args',{});i=r.get('index');cb=a.get('commandBuffer')
 if n=='vkCreateImage':images[a['pImage']]=a['pCreateInfo']
 elif n=='vkCreateImageView':views[a['pView']]=a['pCreateInfo']
 elif n=='vkCreateSampler':samplers[a['pSampler']]=a['pCreateInfo']
 elif n=='vkBeginCommandBuffer':begins[cb]=i
 elif n and n.startswith('vkCmdBeginRendering'):active[cb]=i
 elif n and n.startswith('vkCmdEndRendering'):ends[active.pop(cb)]=i
 elif n=='vkUpdateDescriptorSets':
  for w in a['pDescriptorWrites']:sets.setdefault(w['dstSet'],{})[w['dstBinding']]=w
 elif n=='vkCmdBindDescriptorSets':bound[cb]=a
 elif n=='vkQueueSubmit':
  for s in a['pSubmits']:
   for c in s['pCommandBuffers']:submits[(c,begins[c])]=i
 if i in targets:
  descriptors={}
  for k,v in sets[bound[cb]['pDescriptorSets'][0]].items():
   for im in v.get('pImageInfo')or[]:
    if im['imageView']in views:descriptors[k]=dict(view=im['imageView'],image=views[im['imageView']]['image'])
    if im['sampler']in samplers:descriptors[k]=dict(sampler=im['sampler'],state=samplers[im['sampler']])
  events[i]=dict(name=targets[i],command_buffer=cb,begin_command_buffer=begins[cb],render_begin=active[cb],descriptors=descriptors)
total=0
for i,e in events.items():
 e['queue_submit']=submits[(e['command_buffer'],e['begin_command_buffer'])];e['render_range']=[e['render_begin'],ends[e['render_begin']]];d=draws[i];e['phase']=d['phase'];e['pipeline']=d['pipeline'];e['fragment_module']=next(s['module']for s in pipelines[str(d['pipeline'])]['pStages']if s['stage']=='VK_SHADER_STAGE_FRAGMENT_BIT');e['color_attachments']=[]
 for k,a in enumerate(phases[e['render_begin']]['info']['pColorAttachments']or[]):
  v=views[a['imageView']];ci=images[v['image']];assert ci['format']=='VK_FORMAT_R8G8B8A8_UNORM';w,h=ci['extent']['width'],ci['extent']['height'];n=w*h*4;total+=n;e['color_attachments'].append(dict(index=k,image=v['image'],view=a['imageView'],format=ci['format'],width=w,height=h,raw_bytes=n))
cfg=dict(DumpResourcesOptions=dict(Scale=1.0,ImageFormat='png',DumpBeforeCommand=False,DumpDepth=False,DumpVertexIndexBuffer=False,DumpAllDescriptors=False,DumpAllImageSubresources=False,DumpRawImages=True,DumpSeparateAlpha=False,JsonOutputPerCommand=True,BinaryFileCompressionType='none'),BeginCommandBuffer=[62473],Draw=[sorted(targets)],RenderPass=[sorted(e['render_range']for e in events.values())],QueueSubmit=[76331])
assert all(e['begin_command_buffer']==62473 and e['queue_submit']==76331 for e in events.values())
(Q/'dump-dof-bloom.json').write_text(json.dumps(cfg,indent=2))
command=json.loads((BASE/'prepared-replay-command.json').read_text());argv=command['argv'];prefix=r'C:\Users\rwill\Documents\Opem Amalur\work\v45-foliage-coverage\replay-dump-capability'
argv[argv.index('--dump-resources')+1]=prefix+r'\dof-bloom-plan\dump-dof-bloom.json';argv[argv.index('--dump-resources-dir')+1]=prefix+r'\dof-bloom-output';command.update(status='PREPARED ONLY; parent review required before replay',selected_draws=9,estimated_raw_attachment_bytes=total,output_budget_bytes=32*1048576)
(Q/'prepared-replay-command.json').write_text(json.dumps(command,indent=2))
plan=dict(scope='one additional original-frame replay; only nativeDOF/fuzz/effect and bloom checkpoints',events={str(i):e for i,e in sorted(events.items())},selected_draws=9,raw_bytes=total,output_budget_bytes=32*1048576,depth_and_descriptors=False,sampling_note='Full-resolution requested pixel is sampled directly at x,y for full-size outputs. For lower-resolution intermediate maps, report native texels plus bilinear sampling at the actual consumer UV; do not assume integer divide. UV vertex/half-texel offsets require source inspection and are not inferred by eye.')
(Q/'dof-bloom-stage-plan.json').write_text(json.dumps(plan,indent=2));print(json.dumps(dict(raw_bytes=total,selected_draws=9,events={i:[e['name'],e['render_range'],e['color_attachments']]for i,e in events.items()}),indent=2))
