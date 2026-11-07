from pathlib import Path
import json,struct,hashlib,ctypes,collections
Q=Path(__file__).resolve().parent;R=Q.parent;C=R.parent/'open-amalur-native-camera'
source=json.loads((Q/'source-catalog.json').read_text());possible=set();lookup=collections.defaultdict(list)
for row in source:
 for f in row['files']:
  for l in f['levels']:
   possible.add((f['format'],l['width'],l['height']))
   lookup[(f['format'],l['width'],l['height'],l['sha256'])].append(dict(texture=row['texture'],asset=row['asset'],file=f['path'],source_sha256=f['sha256'],source_level=l['level'],source_levels=f['levels'][l['level']:]))
idx=json.loads((C/'capture-index.json').read_text());pipelines=json.loads((C/'pipeline-index.json').read_text());draws={d['index']:d for d in idx['draws']}
def used(module):
 b=(C/'shaders'/f'module-{module}.spv').read_bytes();w=struct.unpack('<%dI'%(len(b)//4),b);o=5;bindings={};loads=set()
 while o<len(w):
  n=w[o]>>16;op=w[o]&65535;a=w[o+1:o+n]
  if op==71 and len(a)>=3 and a[1]==33:bindings[a[0]]=a[2]
  if op==61:loads.add(a[2])
  o+=n
 return {v for k,v in bindings.items()if k in loads and v>=32}
usage_bindings={}
for pid,p in pipelines.items():
 stages=[s['module']for s in p['pStages']if s['stage']=='VK_SHADER_STAGE_FRAGMENT_BIT']
 if stages:usage_bindings[int(pid)]=used(stages[0])
images={};views={};sets={};bound={};usage=collections.defaultdict(list)
for line in (R/'evidence/dalentarth.jsonl').open():
 try:r=json.loads(line)
 except json.JSONDecodeError:continue
 f=r.get('vkFunc',{});n=f.get('name');a=f.get('args',{});i=r.get('index')
 if n=='vkCreateImage':images[a['pImage']]=a['pCreateInfo']
 elif n=='vkCreateImageView':views[a['pView']]=a['pCreateInfo']
 elif n=='vkUpdateDescriptorSets':
  for v in a['pDescriptorWrites']:sets.setdefault(v['dstSet'],{})[v['dstBinding']]=v
 elif n=='vkCmdBindDescriptorSets':bound[a['commandBuffer']]=a
 if i in draws:
  d=draws[i];bind=bound.get(a['commandBuffer']);bs=usage_bindings.get(d['pipeline'],set())
  if bind:
   for k,v in sets[bind['pDescriptorSets'][0]].items():
    if k not in bs:continue
    for im in v.get('pImageInfo')or[]:
     view=views.get(im['imageView'])
     if view:usage[view['image']].append(dict(draw=i,phase=d['phase'],pipeline=d['pipeline'],binding=k,view_id=im['imageView'],subresourceRange=view['subresourceRange']))
want={i:ci for i,ci in images.items()if ci['arrayLayers']==1 and(ci['format'],ci['extent']['width'],ci['extent']['height'])in possible and usage[i]}
fn=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib').LZ4_decompress_safe;fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int
matched=[];tested=0
with open('/private/tmp/oa-dalentarth-20261105.gfxr','rb')as f:
 _,_,_,n=struct.unpack('<4sIII',f.read(16));f.seek(n*8,1);i=-1
 while h:=f.read(12):
  size,kind=struct.unpack('<QI',h);i+=1;off=f.tell();d=f.read(min(size,48))
  if kind&0x7fffffff==3 and len(d)>=48 and struct.unpack_from('<I',d)[0]&0xffff==8 and struct.unpack_from('<Q',d,20)[0]in want:
   cmd,thread,device,img,nb,aspect,layout,nm=struct.unpack('<IQQQQIII',d);d+=f.read(size-len(d));sizes=struct.unpack_from('<%dQ'%nm,d,48);raw=d[48+8*nm:]
   if kind&0x80000000:
    b=ctypes.create_string_buffer(nb);assert fn(raw,b,len(raw),nb)==nb;raw=b.raw
   assert len(raw)==nb;ci=want[img];fmt=ci['format'];w,h=ci['extent']['width'],ci['extent']['height'];bc3='BC3'in fmt;n=((w+3)//4)*((h+3)//4)*(16 if bc3 else 8);topsha=hashlib.sha256(raw[:n]).hexdigest();hits=lookup.get((fmt,w,h,topsha),[]);tested+=1
   if hits:
    actual=[];o=0
    for lev,stored in enumerate(sizes):
     lw,lh=max(1,w>>lev),max(1,h>>lev);tight=((lw+3)//4)*((lh+3)//4)*(16 if bc3 else 8);assert stored==((tight+511)//512)*512
     actual.append(dict(level=lev,width=lw,height=lh,capture_offset=o,bc_bytes=tight,bc_sha256=hashlib.sha256(raw[o:o+tight]).hexdigest(),capture_stored_bytes=stored));o+=stored
    assert o==len(raw)
    verified=[]
    for hit in hits:
     seq=hit.pop('source_levels');assert len(seq)>=len(actual)
     assert all((l['width'],l['height'],l['sha256'])==(a['width'],a['height'],a['bc_sha256'])for l,a in zip(seq,actual)),(img,hit,'mip-chain mismatch')
     hit['captured_mips_match_source']=True;verified.append(hit)
    matched.append(dict(image=img,block=i,file_offset=off,create_info=ci,aspect=aspect,capture_sha256=hashlib.sha256(raw).hexdigest(),levels=actual,source_matches=verified,active_sampling_draws=usage[img]))
  else:f.seek(size-len(d),1)
(Q/'captured-image-matches.json').write_text(json.dumps(matched,indent=2))
summary=[]
for row in source:
 matches=[(m['image'],m['create_info']['extent'],m['create_info']['mipLevels'],sorted({h['source_level']for h in m['source_matches']if h['texture']==row['texture']}),len(m['active_sampling_draws']))for m in matched if any(h['texture']==row['texture']for h in m['source_matches'])]
 summary.append(dict(texture=row['texture'],asset=row['asset'],captured=matches))
(Q/'capture-match-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps(dict(tested_images=tested,matched_images=len(matched),textures=summary),indent=2))
