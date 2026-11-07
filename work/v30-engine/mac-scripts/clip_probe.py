import struct,re,sys
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur"
b=(root/"work/v20-char/character.bin").read_bytes()
J,C,P,T=struct.unpack_from("<IIII",b,8);o=24;par=struct.unpack_from(f"<{J}h",b,o);o+=J*2+(J%2)*2
print("joints",J,"clips",C)
def qmul(a,b):
    x1,y1,z1,w1=a;x2,y2,z2,w2=b;return (w1*x2+x1*w2+y1*z2-z1*y2,w1*y2-x1*z2+y1*w2+z1*x2,w1*z2+x1*y2-y1*x2+z1*w2,w1*w2-x1*x2-y1*y2-z1*z2)
def rot(q,v):
    t=np.cross(q[:3],v)*2;return np.array(v)+q[3]*t+np.cross(q[:3],t)
clips=[]
for c in range(C):
    fr,fps=struct.unpack_from("<If",b,o);o+=8;A=np.frombuffer(b,"<f4",fr*J*7,o).reshape(fr,J,7);o+=fr*J*28;clips.append((fr,fps,A))
def fk(F):
    W=np.zeros((J,3));Q=[None]*J
    for j in range(J):
        q=tuple(F[j,:4]);t=F[j,4:]
        if par[j]<0:Q[j]=q;W[j]=t
        else:Q[j]=qmul(Q[par[j]],q);W[j]=W[par[j]]+rot(np.array(Q[par[j]]),t)
    return W
for c,name in enumerate(("idle","walk","run")):
    fr,fps,A=clips[c];W=np.array([fk(A[f]) for f in range(fr)])
    z=W[:,:,2];feet=np.argsort(z.mean(0))[:6]
    # the two lowest moving end joints
    move=(W[:,:,:2].max(0)-W[:,:,:2].min(0)).max(1);cand=[j for j in feet if move[j]>5][:2] or list(feet[:2])
    root=W[:,0];pel=W[:,2]
    print(f"{name}: frames {fr} fps {fps:.1f} seconds {(fr-1)/fps:.2f} root travel {np.round(root[-1]-root[0],1).tolist()} pelvis travel {np.round(pel[-1]-pel[0],1).tolist()} pelvis z range {round(float(pel[:,2].min()))}-{round(float(pel[:,2].max()))}")
    print("  loop pop: largest joint jump last-to-first",round(float(np.linalg.norm(W[-1]-W[0],axis=1).max()),1),"typical per-frame",round(float(np.median(np.linalg.norm(np.diff(W,axis=0),axis=2).max(1))),1),"largest frame jump",round(float(np.linalg.norm(np.diff(W,axis=0),axis=2).max()),1))
    for j in cand:
        fz=W[:,j,2];lo=fz<=fz.min()+6;vel=np.diff(W[:,j,:2],axis=0)*fps;speed=np.linalg.norm(vel,axis=1)
        planted=lo[:-1]
        print(f"  foot joint {j} z {fz.min():.0f}-{fz.max():.0f} planted frames {int(planted.sum())}/{fr-1} planted speed in clip {np.median(speed[planted]) if planted.any() else 0:.0f} u/s direction {np.round(np.median(vel[planted],axis=0)).tolist() if planted.any() else ''}")
for c in range(3,C):
    fr,fps,A=clips[c];print("clip",c,fr,round(fps,1),round((fr-1)/fps,2))
