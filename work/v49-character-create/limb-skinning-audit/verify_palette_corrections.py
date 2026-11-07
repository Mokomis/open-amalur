"""Independent stdlib verifier for OACPL01 source-bound prefix corrections; no shared exporter math imports."""
from pathlib import Path
import struct,hashlib,json,math
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');O=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).digest()
class Bad(ValueError):pass
def ck(c,s):
 if not c:raise Bad(s)
def mul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return (w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z)
def conjugate(q):return (-q[0],-q[1],-q[2],q[3])
def rotate(q,p):return mul(mul(q,(*p,0.0)),conjugate(q))[:3]
def skel(b):
 n=struct.unpack_from('<I',b,20)[0];a=28+struct.unpack_from('<i',b,28)[0];pa=32+struct.unpack_from('<i',b,32)[0];na=36+struct.unpack_from('<i',b,36)[0]
 parents=struct.unpack_from('<'+'H'*n,b,pa);names=struct.unpack_from('<'+'I'*n,b,na);world=[]
 for i in range(n):
  s=struct.unpack_from('<12f',b,a+48*i);q=conjugate(s[:4]);t=s[4:7];j=parents[i]
  ck(all(abs(x-1)<1e-5 for x in s[8:11]),'nonunit rig scale outside existing policy')
  if j!=65535:
   ck(j<i,'parent order');pq,pt=world[j];v=rotate(pq,t);q=mul(pq,q);t=tuple(pt[k]+v[k] for k in range(3))
  world.append((q,t))
 return parents,names,world
def parts(b):
 j,c,n,t=struct.unpack_from('<4I',b,8);a=24+((j+1)//2)*4
 for _ in range(c):nf=struct.unpack_from('<I',b,a)[0];a+=8+nf*j*28
 for _ in range(t):w,h=struct.unpack_from('<II',b,a);a+=8+w*h*4
 out=[]
 for i in range(n):
  nv,ni,pc,tx=struct.unpack_from('<IIIi',b,a);a+=16;pal=a;v=a+32*pc;idx=v+52*nv;a=idx+4*ni;out.append((nv,ni,pc,pal,v,idx))
 ck(a==len(b),'base EOF');return out
def validate(data,base):
 ck(len(data)>=64 and data[:8]==b'OACPL01\0','magic/size')
 version,n,covered,rb,pb,z=struct.unpack_from('<6I',data,8)
 ck((version,covered,rb,pb,z)==(1,2,128,32,0),'header')
 ck(data[32:64]==H(base),'base hash')
 pp=parts(base);ck(n==len(pp)==17,'base partcount');a=64;seen=[];plan=[]
 man=json.loads((O/'palette-correction-manifest.json').read_text())
 rigpath=P/'work/v20-inputs/patch_0.pak/456813.fab_bxml';rparents,rnames,rworld=skel(rigpath.read_bytes());rindex={name:i for i,name in enumerate(rnames)}
 for expected in man['corrections']:
  ck(a+128<=len(data),'record truncated')
  at=a;record=data[a:a+128];a+=128
  part,fab,asm,sc,cap,nv,ni,flags=struct.unpack_from('<8I',record)
  ck(part==expected['part'] and part not in seen,'part order');seen.append(part)
  ck((fab,asm)==((660458,0) if part==2 else (660459,1)),'source identity')
  ck(flags==0 and 0<sc<=cap<=96,'record domain')
  pv,pi,pc,pa,vo,io=pp[part];ck((nv,ni,cap)==(pv,pi,pc),'current shape')
  ck(sc==expected['source_count'],'source count')
  ck(a+32*sc<=len(data),'palette truncated')
  payload=data[a:a+32*sc];a+=32*sc
  ck(record[32:64]==H(base[pa:pa+32*pc]),'old palette hash')
  ck(record[64:96]==H(payload),'replacement hash')
  fb=(P/expected['source_fab']).read_bytes()
  ck(record[96:128]==H(fb) and H(fb).hex()==expected['source_fab_sha256'],'source FAB hash')
  sp,sn,sw=skel(fb);d=expected['assembly_descriptor_offset'];ck(struct.unpack_from('<I',fb,d+28)[0]==sc,'source exact remap count')
  golden=bytearray();joined=[]
  for slot in range(sc):
   ro=d+32+52*slot;source_id=struct.unpack_from('<i',fb,ro+48)[0];cur=source_id;chain=[]
   ck(0<=source_id<len(sn),'source bone index')
   while sn[cur] not in rindex:
    chain.append(cur);cur=sp[cur];ck(cur!=65535 and len(chain)<128,'source ancestor mapping')
   joint=rindex[sn[cur]];q,t=rworld[joint];iq=conjugate(q);v=rotate(iq,t);it=tuple(-x for x in v)
   golden+=struct.pack('<I7f',joint,*iq,*it)
   decoded=struct.unpack_from('<I7f',payload,32*slot)
   ck(decoded[0]<len(rnames) and all(math.isfinite(x) for x in decoded[1:]),'replacement values')
   ck(abs(sum(x*x for x in decoded[1:5])-1)<1e-3,'replacement unit quaternion')
   joined.append(dict(slot=slot,source_bone_index=source_id,source_hash=sn[source_id],rig_joint=joint,ancestor_chain=chain))
  ck(payload==golden,'independent source mapping/rest reconstruction')
  for vi in range(nv):
   off=vo+52*vi;joints=base[off+32:off+36];weights=struct.unpack_from('<4f',base,off+36)
   for j,w in zip(joints,weights):
    ck(not(w>0 and j>=sc),'positive weight outside source palette')
  plan.append((pa,payload,32*pc));ck(at==expected['record_offset'],'record offset')
 ck(a==len(data),'EOF')
 # Atomic prefix-only operation on a PRIVATE memory copy, preserving capacity+all other bytes.
 patched=bytearray(base);allowed=set()
 for pa,payload,capacity in plan:
  patched[pa:pa+len(payload)]=payload;allowed.update(range(pa,pa+len(payload)))
 ck(len(patched)==len(base),'no resize')
 changed=[i for i,(x,y) in enumerate(zip(patched,base)) if x!=y]
 ck(all(i in allowed for i in changed),'outside prefix changed')
 return dict(changed_bytes=len(changed),patched_span_bytes=len(allowed),parts=seen,capacity_unchanged=True,all_other_pack_bytes_unchanged=True),plan
def main():
 man=json.loads((O/'palette-correction-manifest.json').read_text());base=(P/man['base_pack']).read_bytes();data=(O/man['sidecar']).read_bytes()
 ck(H(base).hex()==man['base_pack_sha256'],'base pinned')
 result,plan=validate(data,base);negative=[]
 for cut in [0,7,31,63,64,191,192,223,224,351,352,735]:
  try:validate(data[:cut],base);raise AssertionError('accepted truncation')
  except (Bad,struct.error):negative.append('truncate-'+str(cut))
 for name,at in [('magic',0),('version',8),('partCount',12),('covered',16),('recordBytes',20),('paletteBytes',24),('reserved',28),('baseHash',32),('partID',64),('FAB',68),('asm',72),('sourceCount',76),('capacity',80),('vcount',84),('icount',88),('flags',92),('oldHash',96),('newHash',128),('sourceHash',160),('payloadJoint',192),('payloadQuaternion',199),('secondSourceCount',236)]:
  bad=bytearray(data);bad[at]^=128
  try:validate(bytes(bad),base);raise AssertionError('accepted corrupt '+name)
  except (Bad,struct.error):negative.append(name)
 try:validate(data+b'X',base);raise AssertionError('accepted trailer')
 except Bad:negative.append('trailer')
 bad=bytearray(base);bad[100]^=1
 try:validate(data,bytes(bad));raise AssertionError('accepted wrong base')
 except Bad:negative.append('wrong-base')
 result.update(result='PASS',negative_cases=len(negative),negative_case_names=negative,base_pack_sha256=H(base).hex(),sidecar_sha256=H(data).hex(),
  scope='Private-memory atomic prefix test + source reconstruction. No source/base file write; no live renderer change.')
 (O/'palette-validation-receipt.json').write_text(json.dumps(result,indent=2))
 print(json.dumps(result))
if __name__=='__main__':main()
