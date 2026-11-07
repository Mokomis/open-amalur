import json,re,struct,collections,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/rig.txt","w",encoding="utf-8")
def P(*a):print(*a,file=out,flush=True)
mapn=syms.get("ragdoll_bone_mappings",{});nm=lambda v:str(mapn.get(str(v),v))
b=(root/"work/v20-char/character.bin").read_bytes();J,C,Np,Nt=struct.unpack_from("<IIII",b,8);o=24;par=struct.unpack_from(f"<{J}h",b,o);o+=J*2+(J%2)*2
clips=[]
for c in range(C):
    fr,fps=struct.unpack_from("<If",b,o);o+=8;clips.append((fr,fps,np.frombuffer(b,"<f4",fr*J*7,o).reshape(fr,J,7)));o+=fr*J*28
for t in range(Nt):
    w,h=struct.unpack_from("<II",b,o);o+=8+w*h*4
parts=[]
for p in range(Np):
    nv,ni,npal,ti=struct.unpack_from("<IIIi",b,o);o+=16
    pal=[(struct.unpack_from("<I",b,o+k*32)[0],struct.unpack_from("<4f",b,o+k*32+4),struct.unpack_from("<3f",b,o+k*32+20)) for k in range(npal)];o+=npal*32
    V=np.frombuffer(b,dtype=[("p","<3f4"),("n","<3f4"),("t","<2f4"),("j","u1",4),("w","<4f4")],count=nv,offset=o);o+=nv*52;o+=ni*4
    parts.append((pal,V,ti))
fab=(inp/"patch_0.pak/456813.fab_bxml").read_bytes();_,_,names,bind=skeleton(fab)
def qm(a,b):return np.array(qmul(tuple(a),tuple(b)))
def fk(F):
    Q=[None]*J;T=[None]*J
    for j in range(J):
        q,t=F[j,:4],F[j,4:]
        if par[j]<0:Q[j]=np.array(q);T[j]=np.array(t)
        else:Q[j]=qm(Q[par[j]],q);T[j]=T[par[j]]+np.array(rot(tuple(Q[par[j]]),tuple(t)))
    return Q,T
def Rq(q):
    x,y,z,w=q;return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def skin(part,Q,T):
    pal,V,_=part;Ms=[]
    for joint,iq,it in pal:
        q=qm(Q[joint],iq);R=Rq(q);t=np.array(rot(tuple(Q[joint]),tuple(it)))+T[joint];Ms.append((R,t))
    Rs=np.stack([m[0] for m in Ms]);ts=np.stack([m[1] for m in Ms]);r=np.zeros((len(V),3))
    for k in range(4):
        idx=V["j"][:,k];w=V["w"][:,k,None];idx=np.minimum(idx,len(Ms)-1);r+=w*(np.einsum("nij,nj->ni",Rs[idx],V["p"])+ts[idx])
    return r
bq=[np.array(conj(b_[0])) if False else np.array(b_[0]) for b_ in bind];bt=[np.array(b_[1]) for b_ in bind]
P("parts",[(len(p[1]),len(p[0]),p[2]) for p in parts]," z ranges",[(round(float(p[1]["p"][:,2].min())),round(float(p[1]["p"][:,2].max()))) for p in parts])
head=max(range(len(parts)),key=lambda i:(parts[i][1]["p"][:,2].max()>185 and parts[i][1]["p"][:,2].min()>120 and len(parts[i][1])))
P("head part index",head,"joints it uses",collections.Counter(nm(names[parts[head][0][int(x)][0]]) for x,w in zip(parts[head][1]["j"][:,0],parts[head][1]["w"][:,0]) if w>0).most_common(8))
for i,pt in enumerate(parts):
    q=skin(pt,bq,bt);d=np.linalg.norm(q-pt[1]["p"],axis=1);P("part",i,"at the rig's own bind: moved mean",round(float(d.mean()),2),"max",round(float(d.max()),2))
labels=["idle","walk","run","atk1","atk2","atk3","react","death","sword_idle","sword_walk","sword_run","atk4"]
HEAD=[j for j in range(J) if nm(names[j])=="BIP01_HEAD"][0];NECK=par[HEAD];CHEST=par[NECK]
torso=0
def collar(Q,T):
    h=skin(parts[head],Q,T);t=skin(parts[torso],Q,T)
    low=h[h[:,2]<np.percentile(h[:,2],12)];top=t[t[:,2]>np.percentile(t[:,2],90)]
    d=np.linalg.norm(low[:,None,:2]-top[None,:,:2],axis=2).min(1);gap=low[:,2].min()-top[:,2].max()
    return round(float(np.percentile(d,90)),1),round(float(gap),1)
for c,lab in enumerate(labels):
    fr,fps,A=clips[c];rows=[]
    for f in range(0,fr,max(1,fr//4)):
        Q,T=fk(A[f]);R=Rq(Q[HEAD])@Rq(bq[HEAD]).T;g=R@np.array([1,0,0]);u=R@np.array([0,0,1]);rows.append((round(float(np.degrees(np.arcsin(g[2])))),round(float(np.degrees(np.arctan2(u[0],u[2])))),collar(Q,T)))
    P(lab,"frames",fr,"gaze pitch deg (neg=down), head top lean, collar (xy miss, z gap)",rows[:4])
# Pictures
def draw(ax,c,f,title,X0,Y0,S=2.0):
    fr,fps,A=clips[c];Q,T=fk(A[min(f,fr-1)])
    colors=[(200,60,60),(60,160,60),(60,60,200),(200,160,60),(230,230,230),(120,200,220),(200,120,220)]
    for i,pt in enumerate(parts):
        if i!=head and len(pt[1])<100:continue
        q=skin(pt,Q,T)[::2];col=colors[i%len(colors)] if i!=head else (255,255,0)
        for x,y,z in q:
            h=x if ax=="side" else y
            D.point((X0+h*S,Y0-z*S),fill=col)
    D.text((X0-60,Y0+6),title,fill=(255,255,255))
W=1500;H=900;I=Image.new("RGB",(W,H),(20,20,24));D=ImageDraw.Draw(I)
for n,(c,f,t) in enumerate([(0,0,"idle"),(1,8,"walk"),(2,4,"run"),(8,0,"sword idle")]):
    x=150+n*340
    draw("side",c,f,t+" side",x,420);draw("front",c,f,t+" front",x,860)
I.save(root/"work/v21-ui/live/rig.png")
I=Image.new("RGB",(1560,470),(20,20,24));D=ImageDraw.Draw(I)
fr=clips[2][0]
for n in range(8):draw("side",2,n*fr//8,f"run {n}",110+n*190,420)
I.save(root/"work/v21-ui/live/run.png")
I=Image.new("RGB",(1560,940),(20,20,24));D=ImageDraw.Draw(I)
fr=clips[3][0]
for n in range(8):draw("side",3,n*fr//8,f"swing1 {n}",110+n*190,420)
fr=clips[4][0]
for n in range(8):draw("front",4,n*fr//8,f"swing2 {n}",110+n*190,890)
I.save(root/"work/v21-ui/live/atk.png")
# What the game gives a sword carrier
A_=syms["animation"];pat=re.compile(r"player|longsword|1h|_sword|onehand|one_hand",re.I)
loc=[str(v) for v in A_.values() if re.search(r"(idle|walk|run|jog)",str(v),re.I) and pat.search(str(v))]
P("clips",len(loc),sorted(loc)[:90])
ms={int(k):str(v) for k,v in syms["motionset"].items()};P("motionsets player",[v for v in ms.values() if re.search(r"player|longsword|sword|1h",v,re.I)][:50])
for e in ("human_skel","player"):pass
out.close()
