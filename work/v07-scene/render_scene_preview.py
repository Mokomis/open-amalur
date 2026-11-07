"""Windows CPU preview of the exact authored scene.bin supplied to Android."""
import platform,sys,json,struct,hashlib,argparse
from pathlib import Path
assert platform.system()=='Windows'
import numpy as np
from PIL import Image,ImageDraw,ImageFont
sys.path.insert(0,str(Path(__file__).parents[1]/'v07-mesh'))
from render_mesh_preview import panel
root=Path.home()/'Documents'/'Opem Amalur';out=root/'outputs/scene-v07'
ap=argparse.ArgumentParser();ap.add_argument('--scene',type=Path,default=out/'scene.bin');ap.add_argument('--name',default='scene-preview');ap.add_argument('--label',default='77 props · 20 models (2 skinned props omitted)');args=ap.parse_args();assert Path(args.name).name==args.name
data=args.scene.read_bytes()
assert data[:8]==b'OMSC07\0\0';n=struct.unpack_from('<I',data,8)[0];assert len(data)==36+36*n
v=np.frombuffer(data,dtype='<f4',offset=36).reshape(n,9);pos=v[:,:3].astype(float)
# Rotate camera axes only; stored scene data remains unchanged.
a=.65;c=np.cos(a);s=np.sin(a);yaw=np.array([[c,-s,0],[s,c,0],[0,0,1.]])
a=-.7;c=np.cos(a);s=np.sin(a);pitch=np.array([[1,0,0],[0,c,-s],[0,s,c]])
views=[('Top',pos),('Angled',pos@yaw.T@pitch.T)]
image=Image.new('RGB',(1450,855),(248,247,244));draw=ImageDraw.Draw(image);font=ImageFont.truetype(r'C:\Windows\Fonts\segoeui.ttf',23)
draw.text((20,12),'Opem Amalur — Gorhart alchemist shop geometry',font=font,fill=(35,42,48))
draw.text((20,48),f'{args.label} · {n//3:,} triangles · CPU preview of Android asset',font=font,fill=(65,70,75))
records=[]
for i,(name,p) in enumerate(views):
 mesh={'vertex_buffers':[{'positions':p.tolist()}],'index_buffers':[{'indices':list(range(n))}],'assemblies':[{'index':0,'vertex_buffer':0,'index_buffer':0}]}
 tile,receipt=panel(mesh,(0,1,2),700);image.paste(tile,(15+720*i,100));draw.text((30+720*i,110),name,font=font,fill=(35,42,48));records.append(receipt)
draw.text((20,813),'Diagnostic geometry only. Materials, animation and gameplay are not reconstructed.',font=font,fill=(65,70,75))
image.save(out/(args.name+'.png'));(out/(args.name+'.json')).write_text(json.dumps({'scene_sha256':hashlib.sha256(data).hexdigest(),'png_sha256':hashlib.sha256((out/(args.name+'.png')).read_bytes()).hexdigest(),'views':records,'scope':'CPU preview only; not an Android screenshot'},indent=2));print('Preview written')
