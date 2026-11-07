from pathlib import Path
import collections,hashlib,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');Q=P/'work/v45-foliage-coverage/replay-dump-capability';O=Q/'selected-output';A=Q/'analysis';V=A/'previews';V.mkdir(parents=True,exist_ok=True)
plan=json.loads((Q/'dump-stage-plan.json').read_text());sha=lambda b:hashlib.sha256(b).hexdigest();pixels=[(800,150),(980,210),(500,35)];records=[];previews=[];bydraw={};depthproof=[]
for path in sorted(O.glob('*.json')):
 doc=json.loads(path.read_text());d=doc[1];di=d['drawIndex'];stage=plan['events'][str(di)]['name'];entry=dict(draw=di,stage=stage,coordinate_convention='zero-based top-left x,y; raw image row0 is top',attachments=[])
 for att in d.get('colorAttachments',[]):
  fmt=att['format'];sub=att['subresources'][0];w,h,_=sub['dimensions'];f=Path(sub['file']);b=f.read_bytes();dtype='<f2'if fmt=='VK_FORMAT_R16G16B16A16_SFLOAT'else'u1';z=np.frombuffer(b,dtype).reshape(h,w,4);norm=z.astype(np.float32)if dtype=='<f2'else z.astype(np.float32)/255.;name=f'{di}-{stage}-color{att["location"]}';item=dict(role='color',location=att['location'],image=att['imageId'],format=fmt,width=w,height=h,raw_file=str(f),raw_bytes=len(b),raw_sha256=sha(b),samples=[])
  if(w,h)==(1536,864):
   for x,y in pixels:item['samples'].append(dict(pixel=[x,y],rgba_exact=z[y,x].astype(float).tolist(),rgba_normalized=norm[y,x].astype(float).tolist()))
  rgb=np.floor(np.clip(norm[:,:,:3],0.,1.)*255.+.5).astype('u1');im=Image.fromarray(rgb,'RGB');fn=name+'-rgb.png';im.save(V/fn);previews.append(dict(file='previews/'+fn,draw=di,location=att['location'],mapping='RGB clamp0..1 -> nearest8bit; no gamma/resample',raw_sha256=sha(b)))
  bydraw[(di,att['location'])]=im
  if di==69912 and att['location']==2:
   Image.fromarray(np.floor(np.clip(norm[:,:,:3]*4.,0,1)*255+.5).astype('u1'),'RGB').save(V/(name+'-rgb-times4.png'))
  if di in(66881,66891,66901):
   for channel in(0,1):Image.fromarray(z[:,:,channel].astype('u1'),'L').save(V/(name+f'-channel{channel}.png'))
  entry['attachments'].append(item)
 if d.get('depthAttachment'):
  att=d['depthAttachment']
  for sub in att['subresources']:
   f=Path(sub['file']);b=f.read_bytes();w,h,_=sub['dimensions'];item=dict(role=sub['aspect'],image=att['imageId'],format=att['format'],width=w,height=h,raw_file=str(f),raw_bytes=len(b),raw_sha256=sha(b),samples=[])
   if sub['aspect']=='DEPTH'and att['format']=='VK_FORMAT_D24_UNORM_S8_UINT':
    z=np.frombuffer(b,'<u4').reshape(h,w);hi=np.unique(z>>24).tolist();item['high8bit_values']=hi;item['decode']='little-endian24LSB UNORM divided16777215; separate stencil plane'
    assert hi==[0]
    if(w,h)==(1536,864):
     for x,y in pixels:item['samples'].append(dict(pixel=[x,y],raw_u32=int(z[y,x]),depth_unorm=float(z[y,x])/16777215.))
   elif sub['aspect']=='STENCIL'and(w,h)==(1536,864):
    z=np.frombuffer(b,'u1').reshape(h,w)
    for x,y in pixels:item['samples'].append(dict(pixel=[x,y],stencil=int(z[y,x])))
   elif sub['aspect']=='DEPTH'and att['format']=='VK_FORMAT_D16_UNORM':
    z=np.frombuffer(b,'<u2').reshape(h,w);item['decode']='little-endian16bit UNORM divided65535';im=Image.fromarray(np.floor(z.astype(np.float64)/65535.*255+.5).astype('u1'),'L');im.save(V/f'{di}-{stage}-depth.png')
   entry['attachments'].append(item)
 records.append(entry)
final=np.array(bydraw[(73411,0)]);historical=Image.open(P/'work/v31-native-slice/render-20261105/windows-replay.png').convert('RGB');old=np.array(historical);region=(slice(120,600),slice(450,1150));direct=float(np.abs(final[region].astype(float)-old[region].astype(float)).mean());flipped=float(np.abs(final[::-1][region].astype(float)-old[region].astype(float)).mean());assert direct==0 and flipped>1
orientation=dict(row0='top',origin='top-left',historical_original_windows_replay='work/v31-native-slice/render-20261105/windows-replay.png',verification_rectangle_xywh=[450,120,700,480],direct_rgb_mean_absolute_error=direct,vertical_flipped_rgb_mean_absolute_error=flipped,requested_pixels_exact_match=all(np.array_equal(final[y,x],old[y,x])for x,y in pixels))
(A/'pixel-samples.json').write_text(json.dumps(dict(orientation=orientation,pixels=pixels,stages=records),indent=2));(A/'preview-manifest.json').write_text(json.dumps(previews,indent=2))
inventory=[dict(file=str(p.relative_to(O)),bytes=p.stat().st_size,sha256=sha(p.read_bytes()))for p in sorted(O.iterdir())if p.is_file()];(A/'raw-inventory-sha256.json').write_text(json.dumps(dict(files=inventory,total_files=len(inventory),total_bytes=sum(p['bytes']for p in inventory)),indent=2))
font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',18);sheet=Image.new('RGB',(2304,1380),(25,25,25));order=[(69912,0,'G0 encoded normal + gloss'),(69912,1,'G1 albedo + spec'),(69912,2,'G2 ambient RGB (unscaled)'),(66901,0,'Final AO RG'),(72932,0,'Deferred combine'),(72984,0,'Pre fog + water'),(73026,0,'Post fog'),(73214,0,'Post transparents'),(73411,0,'Final AA before HUD')]
for k,(di,loc,label)in enumerate(order):
 im=bydraw[(di,loc)].copy();dr=ImageDraw.Draw(im)
 for j,(x,y)in enumerate(pixels):dr.ellipse((x-7,y-7,x+7,y+7),outline=[(255,64,64),(64,255,64),(64,180,255)][j],width=2)
 im=im.resize((768,432),Image.Resampling.BILINEAR);cx=(k%3)*768;cy=(k//3)*460;sheet.paste(im,(cx,cy+28));ImageDraw.Draw(sheet).text((cx+8,cy+3),f'{di}: {label}',fill='white',font=font)
sheet.save(A/'native-stage-contact-sheet.png')
summary=[]
for e in records:
 for a in e['attachments']:
  if a['role']=='color'and a['samples']:summary.append(dict(draw=e['draw'],stage=e['stage'],location=a['location'],format=a['format'],samples=a['samples']))
(A/'color-pixel-samples.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(dict(stages=len(records),color_previews=len(previews),raw_files=len(inventory),raw_bytes=sum(p['bytes']for p in inventory),orientation=orientation,analysis=str(A)),indent=2))
