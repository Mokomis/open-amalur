"""Offline structural and original-capture correspondence checks. No game run."""
from pathlib import Path
import struct,json,hashlib
import numpy as np
from scipy.spatial import cKDTree
Q=Path(__file__).resolve().parent
DT=np.dtype([('p','<f4',(3,)),('wind','<u4'),('uv','<f4',(2,)),('n','<f4',(3,)),('rgba','u1',(4,))])
assert DT.itemsize==40
rows=[];vertices=[]
for f in sorted((Q/'pack-overlay').glob('g*.bin')):
    b=f.read_bytes();magic,nv,ni,nd=struct.unpack_from('<4s3I',b)
    assert magic==b'OAWF' and ni%3==0
    off=16+nd*12;assert len(b)==off+nv*40+ni*4
    v=np.frombuffer(b,DT,nv,off);ix=np.frombuffer(b,'<u4',ni,off+nv*40)
    assert ni==0 or int(ix.max())<nv
    assert np.isfinite(v['p']).all() and np.isfinite(v['uv']).all() and np.isfinite(v['n']).all()
    assert np.max(abs(np.linalg.norm(v['n'],axis=1)-1))<1e-5
    assert np.all((v['wind']&255)<64) and np.all((v['wind']>>16)==0)
    assert np.all(v['rgba'][:,3]==255)
    draws=[struct.unpack_from('<3I',b,16+i*12) for i in range(nd)]
    assert all(m==254 and first+count<=ni for m,first,count in draws)
    rows.append(dict(file=f.name,vertices=nv,triangles=ni//3,sha256=hashlib.sha256(b).hexdigest()))
    vertices.append(v)
assert len(rows)==18
V=np.concatenate(vertices);P=V['p'].astype(np.float64);P[:,:2]+=102425.0
tree=cKDTree(P);captured=[]
for f in sorted(Q.glob('native-captured-foliage-vb*.bin')):
    b=f.read_bytes();assert len(b)%40==0
    v=np.frombuffer(b,DT);distance,indices=tree.query(v['p'].astype(np.float64));ours=V[indices]
    assert float(distance.max())<0.012
    assert np.array_equal(v['uv'].view('u1'),ours['uv'].copy().view('u1'))
    assert np.array_equal(v['wind'],ours['wind'])
    assert np.array_equal(v['rgba'],ours['rgba'])
    ne=float(np.max(abs(v['n']-ours['n'])));assert ne<5e-6
    captured.append(dict(buffer=f.name,vertices=len(v),sha256=hashlib.sha256(b).hexdigest(),position_error_max=float(distance.max()),position_error_median=float(np.median(distance)),normal_abs_error_max=ne,uv_bytes_exact=True,packed_wind_exact=True,rgba_bytes_exact=True))
assert len(captured)==6 and sum(x['vertices'] for x in captured)==25417
# Independent standard MT19937 port checks the native seed-table source;
# this does not merely compare numpy to itself.
mt=[0]*624;mt[0]=0
for i in range(1,624):mt[i]=(1812433253*(mt[i-1]^(mt[i-1]>>30))+i)&0xffffffff
result=[]
while len(result)<1024:
    for i in range(624):
        y=(mt[i]&0x80000000)|(mt[(i+1)%624]&0x7fffffff)
        mt[i]=mt[(i+397)%624]^(y>>1)^(0x9908b0df if y&1 else 0)
    for y in mt:
        y^=y>>11;y^=(y<<7)&0x9d2c5680;y^=(y<<15)&0xefc60000;y^=y>>18
        result.append(y&0xffffffff)
        if len(result)==1024:break
assert np.array_equal(np.array(result,np.uint32),np.random.RandomState(0).randint(0,2**32,1024,dtype=np.uint32))
report=dict(cells=rows,cell_count=18,total_vertices=len(V),total_triangles=sum(x['triangles'] for x in rows),captured_buffers=captured,captured_vertices=sum(x['vertices'] for x in captured),position_error_units='native world centimetres; position matches within0.12mm',max_position_error=max(x['position_error_max'] for x in captured),independent_mt19937_1024_values_exact=True,limitations=['Placement is independently checked against captured original-game GPU vertices; cross-platform float arithmetic is not x87 bit-exact','No rendering performed by this validator','Native ongoing wind timing is a separate recovered producer; captured palette is specific to reference frame'])
(Q/'overlay-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['cells','captured_buffers']},indent=2))
