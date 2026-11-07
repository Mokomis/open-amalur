import json,struct,hashlib,math,collections
from pathlib import Path
import numpy as np
O=Path(__file__).resolve().parent;R=O.parents[2]
cat=json.loads((O/"appearance-source-catalogue.json").read_text());models={m["fab"]:m for m in cat["models"]}
sha=lambda x:hashlib.sha256(x).hexdigest()
def chunks(b):
 assert b[:8]==b"OAAM001\0";v,sid,total,n,di,r=struct.unpack_from("<6I",b,8);assert v==1 and total==len(b)and di==32
 out={}
 for tag,off,count,stride in struct.iter_unpack("<4sIII",b[di:di+16*n]):
  assert tag not in out and off+count*stride<=len(b);out[tag.decode()]=(off,count,stride)
 return out
def mat(row,runtime=False):
 q=row[4:8]if runtime else row[:4];t=row[:3]if runtime else row[4:7];s=row[8:11];x,y,z,w=[-v for v in q[:3]]+[q[3]]
 m=np.eye(4);m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])*s;m[:3,3]=t;return m
source={}
vertex_count=indices=remap_count=bone_count=pair_count=0;layout=collections.Counter();hashes={}
for sid,m in models.items():
 b=(O/f"models/{sid}.oaam").read_bytes();ch=chunks(b);hashes[str(sid)]=sha(b)
 fb=(R/m["path"]).read_bytes();sb=Path(m["stream"]).read_bytes()
 bo,bn,bs=ch["BONE"];assert bn==struct.unpack_from("<I",fb,20)[0];tp=28+struct.unpack_from("<i",fb,28)[0];pp=32+struct.unpack_from("<i",fb,32)[0];hp=36+struct.unpack_from("<i",fb,36)[0]
 bones=[];world=[]
 for i in range(bn):
  parent=struct.unpack_from("<h",fb,pp+2*i)[0];h=struct.unpack_from("<I",fb,hp+4*i)[0];raw=fb[tp+48*i:tp+48*(i+1)]
  assert b[bo+i*64:bo+i*64+56]==struct.pack("<iI",parent,h)+raw
  row=struct.unpack("<12f",raw);lm=mat(row);world.append(lm if parent<0 or parent==i else world[parent]@lm);bones.append((parent,row));bone_count+=1
 ao,an,st=ch["ASMB"];vo,vn,_=ch["VBUF"];ro,rn,_=ch["RAWV"];co,cn,_=ch["VERT"];io,inn,_=ch["IBUF"];xo,xn,_=ch["INDX"];rmo,rmn,_=ch["RMAP"]
 # source stream cursor independent reader
 na,nv,ni=struct.unpack_from("<3I",sb)if len(sb)>4 else(struct.unpack_from("<I",sb)[0],0,0);cur=12 if len(sb)>4 else 4;assert(na,nv,ni)==(an,vn,inn)
 for vi in range(nv):
  typ,stride,n=struct.unpack_from("<3I",sb,cur);cur+=12;raw=sb[cur:cur+stride*n];cur+=stride*n
  r_at,r_len,vs,nv2,c_at,c_len,vt,flags=struct.unpack_from("<8I",b,vo+32*vi);assert(vs,nv2,vt)==(stride,n,typ)and raw==b[ro+r_at:ro+r_at+r_len]and c_len==96*n
  src=np.ndarray((n,stride),np.uint8,buffer=raw);dst=np.ndarray((n,96),np.uint8,buffer=b,offset=co+c_at)
  assert np.array_equal(src[:,:12],dst[:,:12])and np.array_equal(src[:,12:16],dst[:,12:16])
  weights=np.ndarray((n,3),"<i2",raw,16,(stride,2)).astype(np.float64);weights=np.maximum(-1,weights/32767.).astype("<f4")
  assert np.array_equal(weights.view(np.uint32),np.ndarray((n,3),"<u4",b,co+c_at+16,(96,4)))
  assert np.array_equal(src[:,24:32],dst[:,28:36])
  if stride in[64,68]:assert np.array_equal(src[:,32:40],dst[:,36:44])
  no=40 if stride in[64,68]else 32
  for k in range(3):
   vv=np.maximum(-1,np.ndarray((n,3),"<i2",raw,no+8*k,(stride,2)).astype(np.float64)/32767.).astype("<f4")
   assert np.array_equal(vv.view(np.uint32),np.ndarray((n,3),"<u4",b,co+c_at+44+12*k,(96,4)))
  if stride in[60,68]:
   oc=56 if stride==60 else 64;assert np.array_equal(src[:,oc:oc+4],dst[:,80:84])
  else:assert np.all(dst[:,80:84]==0) # authoredabsence, not inventedwhite
  assert int(src[:,12:16].max(initial=0))<128
  vertex_count+=n;layout[stride]+=1
 for ii in range(ni):
  n=struct.unpack_from("<I",sb,cur)[0];cur+=4;raw=sb[cur:cur+2*n];cur+=2*n;o,n2,sat,slen=struct.unpack_from("<4I",b,io+16*ii)
  assert n==n2 and sat==cur-2*n and slen==2*n
  assert np.array_equal(np.frombuffer(raw,"<u2").astype("<u4"),np.frombuffer(b,"<u4",n,xo+o));indices+=n
 for ai in range(na):
  rawasm=sb[cur:cur+52];cur+=52;ar=struct.unpack_from("<16I",b,ao+ai*128);d=ar[9];nr=struct.unpack_from("<I",fb,d+28)[0]
  assert ar[4]+nr<=rmn and ar[5]==nr;assert b[rmo+52*ar[4]:rmo+52*(ar[4]+nr)]==fb[d+32:d+32+52*nr]
  tail=d+44+nr*52;mid,shader,var,typ=struct.unpack_from("<4I",fb,tail)
  assert ar[2]==mid and ar[11]==typ and ar[12]==fb[tail+24]and ar[13]==shader and ar[14]==var
  assert typ=={56:17,60:22,64:25,68:26}[ar[10]];remap_count+=nr
 assert cur==len(sb)
 # exact authored childmaps raw records, independently walk source serializedprefix
 st=struct.unpack_from("<I",fb)[0];nh=struct.unpack_from("<I",fb,st+4)[0];at=st+8+4*nh;nmap=struct.unpack_from("<I",fb,at)[0];at+=4
 mo,mn,_=ch["CMAP"];po,pn,_=ch["CPAI"];assert nmap==mn;maps=[]
 for mi in range(nmap):
  n=struct.unpack_from("<I",fb,at)[0];pairs=fb[at+4:at+4+12*n];tail=at+4+12*n;alias,slot,flag=struct.unpack_from("<IIB",fb,tail);r=struct.unpack_from("<8I",b,mo+mi*32)
  assert r[1:6]==(n,alias,slot,flag,at)and b[po+r[0]*12:po+(r[0]+n)*12]==pairs
  maps.append([struct.unpack_from("<3i",pairs,i*12)for i in range(n)]);pair_count+=n;at=tail+9
 source[sid]=dict(bones=bones,rest=world,maps=maps)
# Cproductionpose samples vs independent exact source rig/map equations
p=(O/"default-animated-pose-samples.bin").read_bytes();at=0;cases=[];profiles=json.loads((O/"selection-source-receipt.json").read_text())["profiles"]
while at<len(p):
 pi,frame,nc=struct.unpack_from("<3I",p,at);at+=12;worlds=[];maxerr=0.;refs=[]
 clip=(O/f"clips/{profiles[pi]['creator_fab']}-{profiles[pi]['creator_idle_clip']}.local-trs.bin").read_bytes();nj,nf,fps=struct.unpack_from("<IIf",clip)
 for ci in range(nc):
  sid,parent,mi,nb=struct.unpack_from("<IiII",p,at);at+=16;cworld=np.frombuffer(p,"<f4",nb*12,at).astype(np.float64).reshape(nb,3,4);at+=nb*48;s=source[sid]
  if ci==0:
   rows=[struct.unpack_from("<12f",clip,12+(frame*nj+i)*48)for i in range(nj)];world=[]
   for bi,(par,_)in enumerate(s["bones"]):
    local=mat(rows[bi]);world.append(local if par<0 or par==bi else world[par]@local)
  else:
   world=[None]*nb;pa=source[refs[parent]]["maps"][mi]
   for pb,cb,other in pa:assert other==0;world[cb]=worlds[parent][pb].copy()
   for bi,(par,row)in enumerate(s["bones"]):
    if world[bi]is None:world[bi]=mat(row)if par<0 or par==bi else world[par]@mat(row)
  err=float(np.max(np.abs(np.array(world)[:,:3,:]-cworld)));maxerr=max(maxerr,err);assert err<.002,(pi,ci,sid,err)
  worlds.append(world);refs.append(sid)
 cases.append(dict(profile=pi,frame=frame,components=nc,max_abs_matrix_error=maxerr))
receipt=dict(models=len(models),vertices=vertex_count,indices=indices,bones=bone_count,remaps=remap_count,authored_child_pairs=pair_count,layout_counts=dict(layout),all_raw_source_geometry_and_attributes_exact=True,all_authored_map_bytes_exact=True,canonical_native_SNORM_and_UV_RGBA_exact=True,model_sha256=hashes,source_pose_oracle_cases=cases,max_pose_matrix_error=max(r["max_abs_matrix_error"]for r in cases),limits=["CPU matrix algebra reproduces recovered ordinary nativebranch; notbit-identical nativefloatingevaluation","No nativeactive childadditive/override states invented","Ctest1278plans verifies selection/membership/palettes, notoriginal-game visualinspection"])
(O/"independent-validation.json").write_text(json.dumps(receipt,indent=2))
print(json.dumps({k:v for k,v in receipt.items()if k not in["model_sha256","source_pose_oracle_cases"]},indent=2))
