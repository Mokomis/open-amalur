from pathlib import Path
import json,struct,ctypes,hashlib
Q=Path(__file__).resolve().parent;R=Q.parent
C=R.parent/'open-amalur-native-camera'
idx=json.loads((C/'capture-index.json').read_text())
targets={d['index']:d for d in idx['draws'] if d['pipeline'] in (13098,13171)}
sets={};images={};views={};samplers={};bindings={};records=[]
for line in (R/'evidence/dalentarth.jsonl').open():
 try:r=json.loads(line)
 except json.JSONDecodeError:continue
 f=r.get('vkFunc',{});n=f.get('name');a=f.get('args',{});i=r.get('index')
 if n=='vkCreateImage':images[a['pImage']]=a['pCreateInfo']
 elif n=='vkCreateImageView':views[a['pView']]=a['pCreateInfo']
 elif n=='vkCreateSampler':samplers[a['pSampler']]=a['pCreateInfo']
 elif n=='vkUpdateDescriptorSets':
  for w in a['pDescriptorWrites']:sets.setdefault(w['dstSet'],{})[w['dstBinding']]=dict(index=i,**w)
 elif n=='vkCmdBindDescriptorSets':bindings[a['commandBuffer']]=a
 if i in targets:
  d=targets[i];bind=bindings[a['commandBuffer']];entry=dict(draw=d,descriptors={})
  for k,v in sets[bind['pDescriptorSets'][0]].items():
   q=dict(v)
   for im in q.get('pImageInfo')or[]:
    if im['imageView']in views:q['view']=views[im['imageView']];q['image']=images[q['view']['image']]
    if im['sampler']in samplers:q['sampler']=samplers[im['sampler']]
   entry['descriptors'][k]=q
  records.append(entry)
(Q/'grass-capture-bindings.json').write_text(json.dumps(records,indent=2))
want={v['view']['image']:v['image'] for d in records for v in d['descriptors'].values()if v.get('view')}
print('draws',len(records),'images',[(i,c['extent'],c['mipLevels'],c['format'])for i,c in want.items()])
fn=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib').LZ4_decompress_safe
fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int
meta=[]
with open('/private/tmp/oa-dalentarth-20261105.gfxr','rb')as f:
 _,_,_,n=struct.unpack('<4sIII',f.read(16));f.seek(n*8,1);i=-1
 while h:=f.read(12):
  size,kind=struct.unpack('<QI',h);i+=1;off=f.tell();d=f.read(min(size,48))
  if kind&0x7fffffff==3 and len(d)>=48 and struct.unpack_from('<I',d)[0]&0xffff==8 and struct.unpack_from('<Q',d,20)[0]in want:
   cmd,thread,device,img,nb,aspect,layout,nm=struct.unpack('<IQQQQIII',d);d+=f.read(size-len(d));sizes=struct.unpack_from('<%dQ'%nm,d,48);raw=d[48+8*nm:]
   if kind&0x80000000:
    b=ctypes.create_string_buffer(nb);assert fn(raw,b,len(raw),nb)==nb;raw=b.raw
   assert len(raw)==nb
   path=Q/f'image-{img}-aspect{aspect}.bin';path.write_bytes(raw)
   meta.append(dict(image=img,block=i,file_offset=off,stored_bytes=size,bytes=nb,level_sizes=sizes,aspect=aspect,layout=layout,create_info=want[img],sha256=hashlib.sha256(raw).hexdigest()))
  else:f.seek(size-len(d),1)
(Q/'grass-image-provenance.json').write_text(json.dumps(meta,indent=2))
print('extracted',[(m['image'],m['bytes'])for m in meta])
