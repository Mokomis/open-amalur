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
base=yawof(load("human_idle_01")[0][0])[0];print("idle thigh line yaw",round(base,1))
for n in ("human_M_idle_turn_90_left","human_M_idle_turn_90_right","human_M_Idle_Turn_180_Left","Human_M_Idle_Turn_180_Right","Human_Idle_turn_90_Left_Ent_Run","Human_Idle_turn_90_Right_Ent_Run","Human_Idle_turn_180_Right_Ent_Run","human_Run_Turn_180_Short","human_run_start_01","human_run_stop_01","human_M_walk_Start","human_M_walk_stop"):
    R,fps=load(n);y=np.degrees(np.unwrap(np.radians([yawof(f)[0] for f in R])))-base
    pel=[fk(f)[1][1][:2].round(0).tolist() for f in (R[0],R[-1])]
    print(n,len(R),"yaw",y[[0,len(y)//4,len(y)//2,3*len(y)//4,-1]].round(0).tolist(),"j1 xy",pel)
Z,_=load("human_additive_zero");m=len(Z)//2;print("zero j0..3",Z[m,0].round(3).tolist(),Z[m,1].round(3).tolist(),Z[m,5].round(3).tolist())
for n in ("human_run_Slope_Up_Blend","human_run_Slope_Down_Blend","human_run_turn_left_Blend","human_run_turn_Right_Blend","human_Armor_Blend"):
    R,_=load(n);f=R[m];d=np.abs(f-Z[m]);mv=[(j,round(float(d[j,:4].max()),2),round(float(d[j,4:].max()),1)) for j in range(J) if d[j].max()>.02]
    print(n,"frames unique",len({f_.tobytes() for f_ in R}),"moved",len(mv),mv[:14]);
