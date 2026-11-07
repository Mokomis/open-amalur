import json,math,struct
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur"
source=(root/"work/v20-char/build_character.py").read_text()
exec(source[:source.index("# Skeleton and clips")])
main=(inp/"patch_0.pak/456813.fab_bxml").read_bytes()
J,parents,jnames,jworld=skeleton(main)
print(J,list(enumerate(jnames))[:24])
A={v:int(k) for k,v in syms["animation"].items()}
def qm(a,b): return np.array([a[3]*b[0]+a[0]*b[3]+a[1]*b[2]-a[2]*b[1],a[3]*b[1]-a[0]*b[2]+a[1]*b[3]+a[2]*b[0],a[3]*b[2]+a[0]*b[1]-a[1]*b[0]+a[2]*b[3],a[3]*b[3]-a[0]*b[0]-a[1]*b[1]-a[2]*b[2]])
def qr(q,v):
    u=q[:3];t=2*np.cross(u,v);return v+q[3]*t+np.cross(u,t)
def load(n):
    b=(out/f"baked/{A[n]}.bin").read_bytes();j,fr,fps=struct.unpack_from("<IIf",b)
    R=np.frombuffer(b,"<f4",offset=12).reshape(fr*j,12)[:,:7].reshape(fr,j,7).copy();R[:,:,:3]*=-1
    return R,fps
def fk(fr):
    Q=[None]*J;T=[None]*J
    for j in range(J):
        p=parents[j]
        if p>=J or p<0:Q[j]=fr[j,:4];T[j]=fr[j,4:7]
        else:Q[j]=qm(Q[p],fr[j,:4]);T[j]=T[p]+qr(Q[p],fr[j,4:7])
    return np.array(Q),np.array(T)
print("parents",list(parents)[:24]);Q0,T0=fk(load("human_idle_01")[0][0]);print("idle z",T0[:16,2].round(0).tolist(),"x",T0[:16,0].round(0).tolist(),"y",T0[:16,1].round(0).tolist())
L,R_=3,9
def yawof(fr):
    Q,T=fk(fr);d=T[L]-T[R_];return math.degrees(math.atan2(d[1],d[0])),T[0],T[L].round(0)

run,_=load("human_run_01");Z,_=load("human_additive_zero");m=len(Z)//2
def ang(a,b):
    d=abs(float(np.dot(a,b)));return round(math.degrees(2*math.acos(min(1,d))),1)
avg=run.mean(0);avg[:,:4]/=np.linalg.norm(avg[:,:4],axis=1,keepdims=True)
for n in ("human_run_Slope_Up_Blend","human_run_Slope_Down_Blend","human_run_turn_left_Blend","human_run_turn_Right_Blend"):
    R,_=load(n);f=R[m]
    print(n,"to zero",[(j,ang(f[j,:4],Z[m,j,:4])) for j in range(J) if ang(f[j,:4],Z[m,j,:4])>1][:24])
    print("   to run",[(j,ang(f[j,:4],avg[j,:4])) for j in range(1,30)][:30])
    print("   t",f[17,4:7].round(1).tolist(),Z[m,17,4:7].round(1).tolist(),avg[17,4:7].round(1).tolist())
