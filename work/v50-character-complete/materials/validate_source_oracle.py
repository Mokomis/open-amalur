"""Independent NumPy translation of native DXBC, not renderer code reuse."""
from pathlib import Path
import numpy as np,json,csv,hashlib
P=Path(__file__).resolve().parent;f=np.float32;S=64
rows=json.loads((P/'material-catalog.json').read_text());catalog={r['material']:r for r in rows}
xy=(np.arange(S,dtype=np.float32)+f(.5))/f(S)*f(2)-f(1)
xx,yy=np.meshgrid(xy,xy);W=np.stack([xx,yy,np.zeros_like(xx)],-1)
V=np.array([0,0,3],dtype=np.float32)-W;V/=np.sqrt(np.sum(V*V,axis=-1,dtype=np.float32))[...,None]
xyN=np.array([128/255,128/255],dtype=np.float32)*f(2)-f(1)
N=np.array([xyN[0],xyN[1],np.sqrt(f(1)-np.sum(xyN*xyN))],dtype=np.float32)
D=np.array([100,120,140],dtype=np.float32)/f(255);VC=np.array([204,153,255],dtype=np.float32)/f(255);alpha=f(153)/f(255)
CUBE=np.array([80,120,160],dtype=np.float32)/f(255);PROBE=np.array([20,30,40],dtype=np.float32)/f(255)
colors=np.array([[.2+.05*k,.4-.02*k,.6-.03*k,.5] for k in range(8)],dtype=np.float32)
colors[0,0]=f(.08);colors[1,0]=f(.7);colors[2,:3]=[f(.8313726186752319),f(.6823529601097107),f(.6039215922355652)]
results=[]
def half_rtz(v):
 h=v.astype(np.float16)
 return np.where(h.astype(np.float32)>v,np.nextafter(h,np.zeros_like(h),dtype=np.float16),h).astype(np.float32)
for c in csv.DictReader((P/'cases.csv').open()):
 mid=int(c['mid']);m=catalog[mid];kind=m['kind'];i=int(c['case'])
 if kind in [5,7]:continue # legacy world Dot3 smoke only, separate v44 native contract
 co=colors.copy();co[2,3]=f(c['skinA'])
 for slot,col in [(4,'blushA'),(5,'tattooA'),(6,'eyelinerA'),(7,'lipstickA')]:co[slot,3]=f(c[col])
 cutoff=f(m['cutoff_byte'])/f(255)
 mask=f(int(c['mask']))/f(255)
 discarded=kind in [1,3] and mask<cutoff
 if kind==4:
  cosmetic=D+mask*co[3,:3]+PROBE
  base=cosmetic*VC*alpha
  emissive=f(.3) if c['name']=='eye-emissive' else f(m['constant'][0])
  g2=CUBE*alpha*base+cosmetic*VC*mask*emissive
  g2=np.broadcast_to(g2,(S,S,3))
 else:
  fresnel=np.array(m['fresnel'],dtype=np.float32)
  facing=np.clip(np.sum(N*V,axis=-1,dtype=np.float32),f(0),f(1))
  rim=np.clip(fresnel[0]*np.power(f(1)-facing,fresnel[1]),f(0),f(1))
  cosmetic=(co[0,:3]+(co[1,:3]-co[0,:3])*f(64/255)) if kind==3 else (D+(co[2,:3]*D-D)*co[2,3] if kind in [1,2] else D)
  cosmetic=cosmetic+f(m['extra'][0])*rim[...,None]
  if kind==2:
   # VertexUV1=(UV0.y,UV0.x); top-level tile indices are deliberately transposed.
   bx=(np.arange(S)>=S//2).astype(int);by=(np.arange(S)>=S//2).astype(int);tx,ty=np.meshgrid(by,bx);q=tx*2+ty
   makeup=np.array([[255,0,0],[0,255,0],[0,0,255],[64,128,192]],dtype=np.float32)[q]/f(255)
   tattoo=np.array([0,255,64,128],dtype=np.float32)[q]/f(255)
   for slot,channel in [(5,tattoo),(4,makeup[...,0]),(6,makeup[...,1]),(7,makeup[...,2])]:
    weight=channel*co[slot,3];cosmetic=cosmetic+(co[slot,:3]-cosmetic)*weight[...,None]
  base=cosmetic*VC*alpha
  g2=CUBE*alpha*base
  if kind==6:
   tint=np.array([.2,.5,.8],np.float32) if c['name']=='reflect-tint' else np.ones(3,np.float32)
   g2=g2+PROBE*mask*tint
 g2=np.clip(g2,f(0),f(1));h=half_rtz(g2);rgb=np.rint(h*f(255)).astype(np.uint8)
 expected=np.concatenate([rgb,np.full((S,S,1),255,dtype=np.uint8)],axis=-1)
 if discarded:expected[:]=0
 actual=np.frombuffer((P/f'case-{i:02}.rgba').read_bytes(),np.uint8).reshape(S,S,4)
 delta=np.abs(actual.astype(np.int16)-expected.astype(np.int16))
 (P/f'case-{i:02}-oracle.rgba').write_bytes(expected.tobytes())
 results.append(dict(case=i,kind=kind,discarded=bool(discarded),max_delta=int(delta.max()),mismatched_channels=int(np.count_nonzero(delta)),actual_center=actual[32,32].tolist(),oracle_center=expected[32,32].tolist(),actual_sha256=hashlib.sha256(actual.tobytes()).hexdigest(),oracle_sha256=hashlib.sha256(expected.tobytes()).hexdigest()))
summary=dict(cases=len(results),compared_channels=len(results)*S*S*4,max_delta=max(r['max_delta'] for r in results),mismatched_channels=sum(r['mismatched_channels'] for r in results),rounding_qualification='Observed ANGLE nonnegative half towardzero model, previously independently probed; no new universal/native rounding claim.',results=results)
(P/'source-oracle-validation.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='results'}));assert summary['max_delta']<=1
