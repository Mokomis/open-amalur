"""Recover declared SNORM16x4 normal xyz, transform by inverse transpose."""
import struct,math,hashlib,json
from pathlib import Path
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def normal_matrix(point_transform):
 origin=point_transform([0,0,0]);cols=[]
 for i in range(3):
  p=[0,0,0];p[i]=1;q=point_transform(p);cols.append([q[j]-origin[j] for j in range(3)])
 a,b,c=cols;co=[cross(b,c),cross(c,a),cross(a,b)];det=dot(a,co[0])
 if not math.isfinite(det) or abs(det)<1e-12:raise ValueError('Singular normal transformation')
 return [[co[col][row]/det for col in range(3)] for row in range(3)]
class NormalBaker:
 def __init__(self,scene):self.source=scene;self.scene=bytearray(scene);self.recovered=0;self.fallback=0;self.opposed=0;self.changed=0
 def vertex(self,out_index,raw,offset,matrix):
  q=struct.unpack_from('<4h',raw,offset);n=[max(-1.,x/32767.) for x in q[:3]];length=math.sqrt(dot(n,n))
  if not .9<=length<=1.1:self.fallback+=1;return
  n=[dot(row,n) for row in matrix];length=math.sqrt(dot(n,n))
  if not math.isfinite(length) or length<1e-12:raise ValueError('Invalid transformed normal')
  n=[x/length for x in n];at=36+out_index*36+12
  if at+12>len(self.scene):raise ValueError('Normal output span')
  old=struct.unpack_from('<3f',self.source,at)
  if dot(old,n)<-.1:self.opposed+=1
  encoded=struct.pack('<3f',*n);self.changed+=self.source[at:at+12]!=encoded;self.scene[at:at+12]=encoded;self.recovered+=1
 def finish(self,path,report_path):
  path=Path(path);report_path=Path(report_path)
  if path.exists() or report_path.exists():raise ValueError('Preserve prior normal outputs')
  result=bytes(self.scene);count=struct.unpack_from('<I',result,8)[0]
  # Every position and color must retain its original exact float bits.
  if result[:36]!=self.source[:36] or any(result[36+i*36:48+i*36]!=self.source[36+i*36:48+i*36] or result[60+i*36:72+i*36]!=self.source[60+i*36:72+i*36] for i in range(count)):raise ValueError('Normals changed nonnormal scene data')
  report=dict(source_sha256=hashlib.sha256(self.source).hexdigest(),scene_sha256=hashlib.sha256(result).hexdigest(),vertices=count,recovered=self.recovered,unselected=count-self.recovered-self.fallback,invalid_source_fallback=self.fallback,opposed_to_computed_face=self.opposed,changed=self.changed,scope='Native-declared SNORM16x4 xyz normals; inverse transpose of existing reconstruction transforms; native original transform/shader parity not claimed.')
  path.write_bytes(result);report_path.write_text(json.dumps(report,indent=2));return result,report
