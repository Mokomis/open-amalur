from pathlib import Path
import json,struct,ctypes,hashlib,collections
root=Path('/Users/rwillmore/Documents/Codex/2026-11-05');camera=root/'open-amalur-native-camera';packets=root/'open-amalur-native-packets';runtime=root/'open-amalur-native-character/capture-2026-11-05T21-16-24-734Z';j=json.loads((camera/'capture-index.json').read_text());draw=json.loads((runtime/'draw.json').read_text());fn=ctypes.CDLL('/opt/homebrew/lib/liblz4.dylib').LZ4_decompress_safe;fn.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_int,ctypes.c_int];fills=collections.defaultdict(list)
for fill in j['fills']:fills[fill['memory']].append(fill)
results={};f=open('/private/tmp/oa-dalentarth-20261105.gfxr','rb')
for resource in draw['resources']:
 live=(runtime/(resource['name']+'.bin')).read_bytes();matches=[];candidates=[]
 for bid,desc in j['buffers'].items():
  if desc['size']!=len(live):continue
  candidates.append(bid)
  if bid not in j['buffer_memory']:continue
  memory,bind=j['buffer_memory'][bid];map_offset=j['maps'].get(str(memory),[0,0])[0]
  for fill in reversed(fills[memory]):
   start=bind-map_offset-fill['offset'];n=fill['size']
   if start<0 or start+len(live)>n:continue
   f.seek(fill['file_offset']);data=f.read(fill['stored_size'])
   if fill['compressed']:
    buf=ctypes.create_string_buffer(n);assert fn(data[36:],buf,len(data)-36,n)==n;decoded=buf.raw
   else:decoded=data[36:]
   if decoded[start:start+len(live)]==live:matches.append({'buffer_id':int(bid),'memory_id':memory,'fill_block':fill['block'],'memory_offset':bind,'source_bytes':n})
   break
 results[resource['name']]={'engine_token':resource['address'],'bytes':len(live),'sha256':hashlib.sha256(live).hexdigest(),'same_size_candidates':len(candidates),'exact_content_matches':matches}
f.close()
# Independently reconstruct vertex/index binding state at each recorded draw.
cmd={};matched=[];ids={name:{m['buffer_id'] for m in info['exact_content_matches']} for name,info in results.items()}
for number,line in enumerate(open('/private/tmp/oa-dalentarth.jsonl')):
 if number==0:continue
 item=json.loads(line);fun=item.get('vkFunc',{});name=fun.get('name','');a=fun.get('args',{});i=item['index']
 if name=='vkBeginCommandBuffer':cmd[a['commandBuffer']]={'vertex':{}}
 elif name in ['vkCmdBindVertexBuffers','vkCmdBindVertexBuffers2']:
  s=cmd.setdefault(a['commandBuffer'],{'vertex':{}})
  for ix,buf in enumerate(a['pBuffers']):s['vertex'][a['firstBinding']+ix]={'buffer':buf,'offset':a['pOffsets'][ix]}
 elif name=='vkCmdBindIndexBuffer':cmd.setdefault(a['commandBuffer'],{'vertex':{}})['index']=a
 elif name=='vkCmdDrawIndexed' and i>=62468:
  s=cmd[a['commandBuffer']];vertices=s['vertex'];ib=s.get('index',{})
  if all(vertices.get(ix,{}).get('buffer') in ids.get('vertex'+str(ix),set()) for ix in [0,1]) and ib.get('buffer') in ids.get('index',set()):matched.append({'draw_block':i,'args':a,'vertex':{k:dict(v) for k,v in vertices.items()},'index':dict(ib)})
out={'runtime_capture':runtime.name,'method':'exact byte equality of complete D3D resource logical contents against mapped capture-memory ranges; draw binding state independently decoded from captured Vulkan commands','resources':results,'matching_live_draws':matched};(root/'open-amalur-native-character/native-resource-bridge.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
