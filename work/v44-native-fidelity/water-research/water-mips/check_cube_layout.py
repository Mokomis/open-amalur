from pathlib import Path
import json,struct
Q=Path(__file__).resolve().parent;R=Q.parent;s=(R/'make_pack.py').read_text();exec(s[s.index('def decode('):s.index('\ntex=[]')]);results=[]
for tex in json.loads((Q/'water-mip-pack-manifest.json').read_text())['textures']:
 if tex['faces']!=6:continue
 id=tex['image'];raw=(R/'resources'/f'image-{id}-aspect1.bin').read_bytes();previous=None
 for m in tex['levels']:
  w=m['width'];h=m['height'];current=[];wrong=[];off=m['source_level_offset'];fb=m['faces'][0]['source_bc_bytes'];stride=((fb+511)//512)*512
  for face in range(6):current.append(decode(raw[off+face*fb:off+(face+1)*fb],w,h,False));wrong.append(decode(raw[off+face*stride:off+face*stride+fb],w,h,False))
  if previous and stride!=fb:
   correct_error=bad_error=0
   for face in range(6):
    p=previous[face]
    for y in range(h):
     for x in range(w):
      for c in range(3):
       expected=sum(p[(((2*y+dy)*(w*2)+2*x+dx)*4)+c] for dy in [0,1] for dx in [0,1])/4;correct_error+=(current[face][(y*w+x)*4+c]-expected)**2;bad_error+=(wrong[face][(y*w+x)*4+c]-expected)**2
   n=6*w*h*3;results.append(dict(image=id,level=m['level'],width=w,correct_tight_faces_MSE=correct_error/n,incorrect_per_face512_stride_MSE=bad_error/n));assert correct_error<bad_error
  previous=current
(Q/'cube-padding-continuity-check.json').write_text(json.dumps(dict(scope='corroboration only: authored lower levels compared with2x2average of previous authoredlevel; not a mipgeneration step',all_correct_layout_errors_lower=all(x["correct_tight_faces_MSE"]<x["incorrect_per_face512_stride_MSE"] for x in results),levels=results),indent=2));print('Comparisons',len(results))
