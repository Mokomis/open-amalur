"""Strict selected collision-set parser. Root/cell/mesh spans and Bullet input strides statically corroborated."""
from pathlib import Path
import sys,struct,math,hashlib,json,argparse
class CollisionError(ValueError):pass
def parse(data):
 if len(data)<24 or len(data)>32*1024*1024:raise CollisionError('file byte bound')
 payload,tail=struct.unpack_from('<II',data)
 if 8+payload+tail!=len(data) or tail%4:raise CollisionError('carrier lengths')
 end=8+payload;slots=list(struct.unpack_from('<'+'I'*(tail//4),data,end));expected=[];spans=[(8,24)];groups=[]
 if len(slots)>10000 or len(slots)!=len(set(slots)):raise CollisionError('relocation count/duplicates')
 def pair(off,stride,limit):
  if off<8 or off+8>end:raise CollisionError('pair span')
  expected.append(off-8);ptr,count=struct.unpack_from('<II',data,off)
  if count>limit or ptr<24 or ptr+count*stride>end:raise CollisionError('array span')
  if count:spans.append((ptr,ptr+count*stride))
  return ptr,count
 refs,nrefs=pair(8,4,1024)
 if nrefs:raise CollisionError('external collision references need separate resolution')
 gp,gc=pair(16,16,1024)
 for g in range(gc):
  off=gp+g*16;x,y=struct.unpack_from('<ii',data,off);mp,mc=pair(off+8,20,256);meshes=[]
  for m in range(mc):
   off=mp+m*20;tag=struct.unpack_from('<I',data,off)[0];vp,vc=pair(off+4,12,500000);tp,tc=pair(off+12,16,500000)
   vertices=list(struct.iter_unpack('<3f',data[vp:vp+vc*12]));triangles=list(struct.iter_unpack('<4I',data[tp:tp+tc*16]))
   if not vc or not tc:raise CollisionError('empty mesh unadmitted')
   if any(not math.isfinite(c) or abs(c)>10000 for v in vertices for c in v):raise CollisionError('nonfinite/out-of-bound position')
   if any(i>=vc for t in triangles for i in t[:3]):raise CollisionError('triangle index outside vertices')
   meshes.append(dict(tag=tag,vertices=vertices,triangles=triangles))
  groups.append(dict(cell_candidate=[x,y],meshes=meshes))
 if sorted(slots)!=sorted(expected):raise CollisionError('unexpected relocation schema')
 # The selected format tightly packs every root/array once; reject aliases,
 # overlap, unexplained padding and unconsumed payload.
 at=8
 for lo,hi in sorted(spans):
  if lo!=at:raise CollisionError('overlap/gap in payload partition')
  at=hi
 if at!=end:raise CollisionError('unconsumed payload')
 return dict(source_sha256=hashlib.sha256(data).hexdigest(),groups=groups)
def export_scene(parsed,scale):
 if scale!=100:raise CollisionError('only explicit selected-scene scale100 admitted')
 vertices=[]
 for g in parsed['groups']:
  for mesh in g['meshes']:
   for t in mesh['triangles']:
    a,b,c=[mesh['vertices'][i] for i in t[:3]];ab=[b[i]-a[i] for i in range(3)];ac=[c[i]-a[i] for i in range(3)];n=[ab[1]*ac[2]-ab[2]*ac[1],ab[2]*ac[0]-ab[0]*ac[2],ab[0]*ac[1]-ab[1]*ac[0]];length=math.sqrt(sum(x*x for x in n));normal=[x/length for x in n] if length else [0,0,0]
    for v in (a,b,c):vertices.append([x*scale for x in v]+normal+[.5,.5,.5])
 if not vertices or len(vertices)>900000:raise CollisionError('expanded mesh bound')
 lo=[min(v[i] for v in vertices) for i in range(3)];hi=[max(v[i] for v in vertices) for i in range(3)]
 return b'OMSC07\0\0'+struct.pack('<I6f',len(vertices),*lo,*hi)+b''.join(struct.pack('<9f',*v) for v in vertices)
def main():
 import platform
 assert platform.system()=='Windows','process original artifacts on Windows'
 p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
 if a.output.exists() or a.report.exists():raise CollisionError('preserve prior outputs')
 b=a.input.read_bytes();x=parse(b);scene=export_scene(x,100);a.output.write_bytes(scene)
 report=dict(source=str(a.input),source_sha256=x['source_sha256'],output_sha256=hashlib.sha256(scene).hexdigest(),groups=len(x['groups']),meshes=sum(len(g['meshes']) for g in x['groups']),triangles=(len(scene)-36)//108,scale=100,scope='Recovered static collision triangles: native d70a00 confirms cells16/meshes20 and bounds scale100; d69880 confirms Bullet vertex12/triangle16. Authored controller does not reproduce complete native physics.')
 a.report.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
