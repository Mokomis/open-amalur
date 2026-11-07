from pathlib import Path
import json,math,struct
P=Path(__file__).resolve().parent
A=json.loads((P/'particle-coverage.json').read_text());pix=(P/'236125-mip0.rgba').read_bytes();pts={'980210':(980.5,210.5),'800150':(800.5,150.5),'50035':(500.5,35.5)}
def tex(uv):
 x,y=uv[0]*128-.5,uv[1]*128-.5;ix,iy=math.floor(x),math.floor(y);fx,fy=x-ix,y-iy
 return sum(pix[(((iy+dy)%128)*128+(ix+dx)%128)*4+1]/255*(fx if dx else 1-fx)*(fy if dy else 1-fy) for dx in [0,1] for dy in [0,1])
out=[]
for r in A:
 if r['draw'] not in [73194,73063]:continue
 m=r['nativeWVP'];v=r['world_positions'];cl=[tuple(sum(p[k]*m[k*4+j] for k in range(3))+m[12+j] for j in range(4)) for p in v];s=[((c[0]/c[3]+1)*768,(1-c[1]/c[3])*432) for c in cl]
 for hit in r['hits']:
  k=hit['triangle']*3;ss=s[k:k+3];(a,b,c)=ss;x,y=pts[hit['point']];area=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);q=((b[0]-x)*(c[1]-y)-(b[1]-y)*(c[0]-x))/area;rr=((c[0]-x)*(a[1]-y)-(c[1]-y)*(a[0]-x))/area;bc=[q,rr,1-q-rr];iw=sum(bc[i]/cl[k+i][3] for i in range(3));wt=[bc[i]/cl[k+i][3]/iw for i in range(3)];fog=sum(wt[i]*min(math.exp(-(4.731020089820959e-5*cl[k+i][3]-.1552170217037201)),1) for i in range(3));alpha=tex(hit['UV'])*hit['VC'][3]*fog;rgb=[a*alpha*255 for a in hit['VC'][:3]];out.append({'draw':r['draw'],'point':hit['point'],'triangle':hit['triangle'],'clockwiseScreen':area>0,'particleNativeClipZ':sum(wt[i]*cl[k+i][2] for i in range(3)),'clipW':hit['clipW'],'sampleMaskG128Bilinear':tex(hit['UV']),'interpolatedFogTransmission':fog,'effectiveAlphaAssumingSoftFade1':alpha,'additiveRGB8BeforeTargetRounding':rgb})
sums={p:[sum(r['additiveRGB8BeforeTargetRounding'][i] for r in out if r['point']==p) for i in range(3)] for p in pts};(P/'additive-point-upper-bounds.json').write_text(json.dumps({'assumption':'Mip0 bilinear, no occlusion and soft fade=1. Source/native mip identity proven; native depth test not evaluated here. All covered triangles clockwise and survive captured clockwise/back-cull.','perTriangle':out,'sumRGB8':sums},indent=2));print(json.dumps(sums,indent=2))
