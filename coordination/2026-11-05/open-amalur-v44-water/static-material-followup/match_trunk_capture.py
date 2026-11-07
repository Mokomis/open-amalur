from pathlib import Path
import struct,json,ctypes,hashlib,collections
Q=Path(__file__).resolve().parent;S=Q.parent.parent/'open-amalur-native-camera';H=json.loads((Q/'trunk-source-vb-hashes.json').read_text());sizes={x['bytes'] for x in H};hashes={x['sha256']:x for x in H};fn=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib').LZ4_decompress_safe;fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fn.restype=ctypes.c_int;matched={}
with open('/private/tmp/oa-dalentarth-20261105.gfxr','rb') as f:
 _,_,_,n=struct.unpack('<4sIII',f.read(16));f.seek(n*8,1);i=-1
 while h:=f.read(12):
  size,k=struct.unpack('<QI',h);i+=1;off=f.tell();d=f.read(min(size,36))
  if k&0x7fffffff==3 and len(d)>=36 and struct.unpack_from('<I',d)[0]&0xffff==7 and struct.unpack_from('<Q',d,28)[0] in sizes:
   _,thread,dev,buffer,bytes_=struct.unpack('<IQQQQ',d);d+=f.read(size-len(d));raw=d[36:]
   if k&0x80000000:
    out=ctypes.create_string_buffer(bytes_);assert fn(raw,out,len(raw),bytes_)==bytes_;raw=out.raw
   hsh=hashlib.sha256(raw).hexdigest()
   if hsh in hashes:matched[buffer]=dict(buffer=buffer,block=i,source=hashes[hsh])
  else:f.seek(size-len(d),1)
I=json.loads((S/'capture-index.json').read_text());targets={d['index']:d for d in I['draws'] if d['phase']==97};vb={};ans=[]
for l in (Q.parent/'evidence/dalentarth.jsonl').open():
 try:r=json.loads(l)
 except:continue
 f=r.get('vkFunc',{});a=f.get('args',{});n=f.get('name','')
 if n.startswith('vkCmdBindVertexBuffers'):vb[a['commandBuffer']]=a
 if r.get('index') in targets:
  d=targets[r['index']];v=vb.get(a['commandBuffer'],{});b=(v.get('pBuffers') or [None])[0]
  if b in matched:ans.append(dict(draw=d,vertex_bind=v,source_match=matched[b]))
(Q/'trunk-capture-correspondence.json').write_text(json.dumps(ans,indent=2));print('buffers',list(matched),'draws',len(ans),'pipelines',collections.Counter(d['draw']['pipeline'] for d in ans))
