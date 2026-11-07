"""Windows-only CPU geometry preview; raw native coordinates, no material claim."""
import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
assert platform.system() == 'Windows', 'Render selected game geometry on Windows'
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def panel(mesh, axes, size=480):
    width=height=size
    canvas=np.full((height,width,3),235,dtype=np.uint8)
    depth=np.full((height,width),-np.inf,dtype=np.float64)
    all_positions=np.asarray([p for b in mesh['vertex_buffers'] for p in b['positions']],dtype=np.float64)
    if not len(all_positions):return Image.fromarray(canvas),{'drawn_triangles':0,'visible_pixels':0}
    minimum=all_positions.min(axis=0);maximum=all_positions.max(axis=0)
    horizontal,vertical,forward=axes
    center=(minimum+maximum)/2
    span=max(maximum[horizontal]-minimum[horizontal],maximum[vertical]-minimum[vertical],1e-9)
    scale=(size-48)/span
    palettes=np.asarray([[85,130,160],[177,132,76],[113,147,104],[153,112,160],[178,114,109]],dtype=float)
    light=np.asarray([0.3,-0.5,0.8]);light/=np.linalg.norm(light)
    drawn=degenerate=0
    for assembly in mesh['assemblies']:
        vertices=np.asarray(mesh['vertex_buffers'][assembly['vertex_buffer']]['positions'],dtype=np.float64)
        indices=mesh['index_buffers'][assembly['index_buffer']]['indices']
        projected=np.column_stack(((vertices[:,horizontal]-center[horizontal])*scale+width/2,
                                   height/2-(vertices[:,vertical]-center[vertical])*scale,
                                   vertices[:,forward]))
        base=palettes[assembly['index']%len(palettes)]
        for i in range(0,len(indices),3):
            ids=indices[i:i+3];tri=projected[ids];world=vertices[ids]
            x0,y0,z0=tri[0];x1,y1,z1=tri[1];x2,y2,z2=tri[2]
            denom=(y1-y2)*(x0-x2)+(x2-x1)*(y0-y2)
            if abs(denom)<1e-10:degenerate+=1;continue
            left=max(0,int(math.floor(min(tri[:,0]))));right=min(width-1,int(math.ceil(max(tri[:,0]))))
            top=max(0,int(math.floor(min(tri[:,1]))));bottom=min(height-1,int(math.ceil(max(tri[:,1]))))
            if left>right or top>bottom:continue
            yy,xx=np.mgrid[top:bottom+1,left:right+1];xx=xx+0.5;yy=yy+0.5
            a=((y1-y2)*(xx-x2)+(x2-x1)*(yy-y2))/denom
            b=((y2-y0)*(xx-x2)+(x0-x2)*(yy-y2))/denom
            c=1-a-b
            zz=a*z0+b*z1+c*z2
            region=depth[top:bottom+1,left:right+1]
            mask=(a>=-1e-9)&(b>=-1e-9)&(c>=-1e-9)&(zz>region)
            if not mask.any():continue
            normal=np.cross(world[1]-world[0],world[2]-world[0]);length=np.linalg.norm(normal)
            shading=0.45+0.55*(abs(np.dot(normal/length,light)) if length>0 else 0)
            color=np.clip(base*shading,0,255).astype(np.uint8)
            region[mask]=zz[mask]
            canvas[top:bottom+1,left:right+1][mask]=color
            drawn+=1
    return Image.fromarray(canvas),{'drawn_triangles':drawn,'projected_degenerate_triangles':degenerate,
                                    'visible_pixels':int(np.isfinite(depth).sum()),'pixels_per_native_unit':scale}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh_json',type=Path);parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--receipt',type=Path);parser.add_argument('--size',type=int,default=480)
    args=parser.parse_args()
    if not 128<=args.size<=1024:raise ValueError('preview size must be128..1024')
    mesh=json.loads(args.mesh_json.read_text(encoding='utf-8'))
    assert mesh['complete_consumption'] and mesh['schema_version']==1
    width=args.size*3+40;height=args.size+125
    output=Image.new('RGB',(width,height),(248,247,244));draw=ImageDraw.Draw(output)
    font_path=Path(r'C:\Windows\Fonts\segoeui.ttf')
    title=ImageFont.truetype(str(font_path),24) if font_path.exists() else ImageFont.load_default()
    label=ImageFont.truetype(str(font_path),17) if font_path.exists() else ImageFont.load_default()
    draw.text((16,12),'Opem Amalur — extracted geometry',fill=(35,42,48),font=title)
    summary=mesh['summary']
    draw.text((16,48),f"{summary['vertices']:,} vertices · {summary['triangles_in_buffers']:,} triangles · {summary['assemblies']} assemblies",fill=(60,67,72),font=label)
    views=[]
    for index,(name,axes) in enumerate([('XY / top',(0,1,2)),('XZ / front',(0,2,1)),('YZ / side',(1,2,0))]):
        image,record=panel(mesh,axes,args.size)
        x=10+index*(args.size+10)
        output.paste(image,(x,80));draw.text((x+12,88),name,fill=(40,45,50),font=label)
        views.append({'name':name,'axes':list(axes),**record})
    draw.text((16,height-32),'Geometry-only diagnostic; native axes unchanged. Colors and lighting are preview aids, not recovered materials.',fill=(74,78,82),font=label)
    args.output.parent.mkdir(parents=True,exist_ok=True);output.save(args.output)
    receipt={'scope':'Windows CPU rasterization of decoded native position/index buffers; no native renderer/material equivalence claim.',
             'source_game_sha256':mesh['input_sha256'],'mesh_json_sha256':digest(args.mesh_json),
             'renderer_sha256':digest(Path(__file__)),'image':str(args.output),'image_sha256':digest(args.output),
             'image_size':[width,height],'views':views,'backface_culling':False,'depth_test':True,
             'world_placement_applied':False,'materials_recovered':False}
    receipt_path=args.receipt or args.output.with_suffix('.json')
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
