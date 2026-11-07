from pathlib import Path
import hashlib,io,json,struct,math
from PIL import Image
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');Q=P/'work/v44-native-fidelity/water-research/static-authored-mips';W=Q/'world';W.mkdir(parents=True,exist_ok=True)
source=json.loads((Q/'source-catalog.json').read_text());matches=json.loads((Q/'captured-image-matches.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest();outputs=[]
def decode(b,w,h,bc3):
 header=[124,0x81007,h,w,len(b),0,1]+[0]*11+[32,4,int.from_bytes(b'DXT5'if bc3 else b'DXT1','little'),0,0,0,0,0]+[0x1000,0,0,0,0]
 return Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*header)+b)).convert('RGBA').tobytes()
for row in source:
 tid=row['texture'];hitrows=[]
 for m in matches:
  for hit in m['source_matches']:
   if hit['texture']==tid:hitrows.append((m,hit))
 captured=bool(hitrows)
 if captured:
  assert len(set((m['create_info']['extent']['width'],m['create_info']['extent']['height'],m['create_info']['mipLevels'])for m,h in hitrows))==1,(tid,'multiple residency shapes')
  m,hit=min(hitrows,key=lambda mh:mh[1]['source_level']);f=next(f for f in row['files']if f['path']==hit['file']);start=hit['source_level'];count=m['create_info']['mipLevels'];levels=f['levels'][start:start+count]
 else:
  # Unknown GPU residency: keep existing base dimensions, use the complete
  # original authored chain whose own base matches those dimensions.
  old=row['old_texture']['source'];candidates=[f for f in row['files']if(f['width'],f['height'])==(old['width'],old['height'])]
  assert candidates,(tid,'no authored chain at existing base dimensions')
  f=max(candidates,key=lambda f:f['mips']);start=0;levels=f['levels'];count=len(levels)
 raw=Path(f['path']).read_bytes();assert sha(raw)==f['sha256'];parts=[];proof=[]
 for level,info in enumerate(levels):
  bc=raw[info['offset']:info['offset']+info['bytes']];assert sha(bc)==info['sha256']
  rgba=decode(bc,info['width'],info['height'],'BC3'in f['format']);assert len(rgba)==info['width']*info['height']*4
  if captured:assert info['sha256']==m['levels'][level]['bc_sha256']
  parts.append(struct.pack('<I',len(rgba))+rgba);proof.append(dict(level=level,width=info['width'],height=info['height'],source_file_level=info['level'],source_offset=info['offset'],source_bc_bytes=len(bc),source_bc_sha256=sha(bc),capture_bc_sha256=m['levels'][level]['bc_sha256']if captured else None,rgba_sha256=sha(rgba)))
 w,h=levels[0]['width'],levels[0]['height'];blob=struct.pack('<4s4I',b'OATX',0x8058,w,h,count)+b''.join(parts);out=W/f't{tid}.bin';out.write_bytes(blob)
 # Independently parse the file just written and verify every level framing/hash.
 reread=out.read_bytes();assert struct.unpack_from('<4s4I',reread)==(b'OATX',0x8058,w,h,count);o=20
 for level,p in enumerate(proof):
  n=struct.unpack_from('<I',reread,o)[0];o+=4;assert n==p['width']*p['height']*4;assert sha(reread[o:o+n])==p['rgba_sha256'];o+=n
 assert o==len(reread) and reread==blob and sha(Path(f['path']).read_bytes())==f['sha256']
 live=P/'work/v44-native-fidelity/integrated-world'/f't{tid}.bin';previous=live.read_bytes();oldshape=struct.unpack_from('<4I',previous,4)
 highest=max(max(ff['width'],ff['height'])for ff in row['files']);resident_offset=int(round(math.log2(highest/max(w,h))))
 outputs.append(dict(texture_id=tid,asset=row['asset'],kind=row['kind'],file=f'world/t{tid}.bin',format='OATX RGBA8',width=w,height=h,mips=count,bytes=len(blob),sha256=sha(blob),previous_sha256=sha(previous),previous_format_width_height_mips=list(oldshape),source_file=f['path'],source_file_sha256=f['sha256'],source_file_first_level=start,resident_offset_from_highest_available_source=resident_offset,captured_identity=captured,provenance='actual actively sampled captured image; every BC mip SHA-matches original source'if captured else'original authored source mip chain at unchanged current base dimensions; GPU residency not captured',captured_images=sorted(set(mm['image']for mm,hh in hitrows)),captured_image_views=sorted(set(u['view_id']for mm,hh in hitrows for u in mm['active_sampling_draws'])),material_users=row['material_users'],levels=proof))
 print(tid,row['asset'],w,h,count,'captured'if captured else'source-only',flush=True)
assert len(outputs)==19 and set(r['texture_id']for r in outputs)==set(range(658,677))
manifest=dict(scope='replace only native-only texture IDs658..676; no live promotion',new_texture_ids=False,texture_count_change=False,material_profile_change=False,generated_mips=False,resampled_images=False,decoder='Pillow original BC1/BC3 mip payload to RGBA8 independently per level',captured_texture_count=sum(r['captured_identity']for r in outputs),source_only_texture_count=sum(not r['captured_identity']for r in outputs),decoded_mip_count=sum(r['mips']for r in outputs),rgba_bytes=sum(r['bytes']-20-r['mips']*4 for r in outputs),outputs=outputs)
(Q/'merge-plan.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({k:v for k,v in manifest.items()if k!='outputs'},indent=2))
