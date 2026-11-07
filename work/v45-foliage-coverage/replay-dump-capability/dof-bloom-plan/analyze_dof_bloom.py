from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image,ImageDraw,ImageFont
P=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v45-foliage-coverage\replay-dump-capability');Q=P/'dof-bloom-plan';A=Q/'analysis';V=A/'previews';V.mkdir(parents=True,exist_ok=True);O=P/'dof-bloom-output';plan=json.loads((Q/'dof-bloom-stage-plan.json').read_text());points=[(800,150),(980,210),(500,35)];custom=[[73,69,43,91],[74,69,37,97],[109,125,145,178]];rows=[];ims={}
for f in sorted(O.glob('*.json')):
 d=json.loads(f.read_text())[1];a=d['colorAttachments'][0];s=a['subresources'][0];w,h,_=s['dimensions'];raw=Path(s['file']).read_bytes();z=np.frombuffer(raw,'u1').reshape(h,w,4);samples=[]
 for j,(x,y)in enumerate(points):
  u,v=(x+.5)/1536,(y+.5)/864;xx,yy=u*w-.5,v*h-.5;x0,y0=int(np.floor(xx)),int(np.floor(yy));fx,fy=xx-x0,yy-y0;taps=[];value=np.zeros(4,float)
  for dx,dy,weight in [(0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),(0,1,(1-fx)*fy),(1,1,fx*fy)]:
   tx,ty=np.clip(x0+dx,0,w-1),np.clip(y0+dy,0,h-1);rgba=z[ty,tx];value+=rgba*weight;taps.append(dict(texel=[int(tx),int(ty)],weight=weight,rgba=rgba.tolist()))
  sample=dict(fullres_pixel=[x,y],consumer_uv=[u,v],continuous_source_texel=[xx,yy],bilinear_rgba_u8_equivalent=value.tolist(),bilinear_rgba_normalized=(value/255).tolist(),nearest_texel=[int(np.floor(u*w)),int(np.floor(v*h))],nearest_rgba=z[int(np.floor(v*h)),int(np.floor(u*w))].tolist(),bilinear_contributors=taps)
  if d['drawIndex']==73262:sample['root_current_reported_RGBA']=custom[j];sample['current_minus_native_RGBA']=(np.array(custom[j])-z[y,x]).astype(int).tolist()
  samples.append(sample)
 name=plan['events'][str(d['drawIndex'])]['name'];rows.append(dict(draw=d['drawIndex'],stage=name,image=a['imageId'],format=a['format'],dimensions=[w,h],raw_file=s['file'],raw_sha256=hashlib.sha256(raw).hexdigest(),samples=samples));im=Image.fromarray(z[:,:,:3],'RGB');im.save(V/f'{d["drawIndex"]}-{name}-RGB.png');Image.fromarray(z[:,:,3],'L').save(V/f'{d["drawIndex"]}-{name}-A.png');ims[d['drawIndex']]=im
result=dict(coordinates='zero-based top-left, verified in prior selected replay against historical original image',uv_contract='VS1838/1848/1856: UV=clip.xy*(.5,-.5)+.5, clipw1; original six-vertex quad, no authored halftexel offset. Ideal pixel-center UV=(x+.5,y+.5)/(1536,864). CPU bilinear values use exact rational four-tap weights; native NEAREST depth ties are audited separately.',stages=rows)
(A/'native-dof-bloom-pixel-samples.json').write_text(json.dumps(result,indent=2))
font=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',18);sheet=Image.new('RGB',(2304,1380),(25,25,25))
for k,row in enumerate(rows):
 im=ims[row['draw']].resize((768,432),Image.Resampling.BILINEAR);cx=(k%3)*768;cy=(k//3)*460;sheet.paste(im,(cx,cy+28));ImageDraw.Draw(sheet).text((cx+6,cy+3),f"{row['draw']}: {row['stage']}",fill='white',font=font)
sheet.save(A/'dof-bloom-contact-sheet.png');print('analysis',A,'stages',len(rows))
