import json,struct,sys
from pathlib import Path
import numpy as np
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
mapn=syms.get("ragdoll_bone_mappings",{})
nm=lambda v:str(mapn.get(str(v),v))
A={}
for f in (456813,467100):
    fb=extract([f"{f}.fab_bxml"])[f"{f}.fab_bxml"].read_bytes();A[f]=skeleton(fb);print(f,"joints",A[f][0])
J,par,names,world=A[456813];J2,par2,names2,world2=A[467100]
print("same names order",names==names2,"same parents",par==par2,"bind diff max",round(max(max(abs(world[i][1][k]-world2[i][1][k]) for k in range(3)) for i in range(min(J,J2))),2))
diff=[(i,nm(names[i]),nm(names2[i])) for i in range(min(J,J2)) if names[i]!=names2[i]];print("differ",diff[:14])
print("joint list",[(i,nm(names[i]),par[i],[round(x) for x in world[i][1]]) for i in range(J) if world[i][1][2]>120][:36])
b=(root/"work/v20-char/character.bin").read_bytes();J0,C,Pc,Tc=struct.unpack_from("<IIII",b,8);o=24+J0*2;clips=[]
for c in range(C):
    fr,fps=struct.unpack_from("<If",b,o);o+=8;clips.append((fr,fps,np.frombuffer(b,"<f4",fr*J0*7,o).reshape(fr,J0,7)));o+=fr*J0*28
labels=["idle","walk","run","atkb","atks","atkx","react","death","c_idle","c_walk","c_run"]
def fk(F):
    W=[None]*J0
    for j in range(J0):
        q,t=tuple(F[j,:4]),tuple(F[j,4:])
        if par[j]==0xffff:W[j]=(q,t)
        else:
            pq,pt=W[par[j]];v=rot(pq,t);W[j]=(qmul(pq,q),tuple(pt[k]+v[k] for k in range(3)))
    return W
top=max(range(J0),key=lambda j:world[j][1][2])
chain=[];c=top
while c!=0xffff:chain.append(c);c=par[c]
print("head chain",[(j,nm(names[j])) for j in chain])
head=next((j for j in chain if "head" in nm(names[j]).lower()),chain[1]);neck=par[head];chest=par[neck]
print("head",head,nm(names[head]),"neck",neck,nm(names[neck]),"chest",chest,nm(names[chest]))
for c in (0,1,2,8,9,10):
    fr,fps,A_=clips[c];rows=[]
    for f in range(0,fr,max(1,fr//6)):
        W=fk(A_[f]);hq,ht=W[head];nq,nt=W[neck];cq,ct=W[chest]
        fwd=rot(hq,(0,0,1));up=rot(cq,(0,0,1));chin=(np.array(ht)-np.array(ct));rows.append((np.round(ht,0).tolist(),round(float(np.degrees(np.arctan2(chin[0],chin[2])))),round(float(np.linalg.norm(np.array(ht)-np.array(nt))),1)))
    print(labels[c],"frames",fr,"head xyz, lean deg forward, head-neck len",rows[:3])
print("bind head",np.round(world[head][1],0),"neck",np.round(world[neck][1],0),"chest",np.round(world[chest][1],0))
# Local pose differences from bind at neck and head.
for j in (chest,neck,head):
    print(nm(names[j]),"local t per clip",[np.round(clips[c][2][0,j,4:],1).tolist() for c in (0,2,10)])
