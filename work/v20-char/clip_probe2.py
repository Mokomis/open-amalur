import json,math,struct
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";out=root/"work/v20-char"
exec(open(out/"build_character.py").read().split("# Parts and textures")[0].split("# Skeleton and clips")[0].split("_anim = lambda")[0].split("import amalur_mesh")[0])
syms=json.loads((root/"work/v20-inputs/symbols.json").read_text())
A={v:int(k) for k,v in syms["animation"].items()}
def qm(a,b):
    return np.array([a[3]*b[0]+a[0]*b[3]+a[1]*b[2]-a[2]*b[1],a[3]*b[1]-a[0]*b[2]+a[1]*b[3]+a[2]*b[0],a[3]*b[2]+a[0]*b[1]-a[1]*b[0]+a[2]*b[3],a[3]*b[3]-a[0]*b[0]-a[1]*b[1]-a[2]*b[2]])
def load(n):
    b=(out/f"baked/{A[n]}.bin").read_bytes();j,fr,fps=struct.unpack_from("<IIf",b)
    R=np.frombuffer(b,"<f4",offset=12).reshape(fr*j,12)[:,:7].reshape(fr,j,7).copy();R[:,:,:3]*=-1
    return R,fps
def fwd(q):
    # world image of the local axis that points forward at frame 0 in the idle clip is unknown: report yaw of x axis
    x,y,z,w=q;return np.array([1-2*(y*y+z*z),2*(x*y+z*w),2*(x*z-y*w)]),np.array([2*(x*y-z*w),1-2*(x*x+z*z),2*(y*z+x*w)])
Z,_=load("human_additive_zero");print("zero frame spread",np.abs(Z-Z[0]).max())
for n in ("human_run_Slope_Up_Blend","human_run_Slope_Down_Blend","human_run_turn_left_Blend","human_run_turn_Right_Blend"):
    R,_=load(n);mid=R[len(R)//2]
    d=np.abs(mid-Z[len(Z)//2]);print(n,"frames differ first/mid/last",np.abs(R[0]-R[5]).max().round(2),np.abs(R[-1]-R[5]).max().round(2),"joints moved rot",int((d[:,:4].max(1)>.01).sum()),"tr",int((d[:,4:].max(1)>.5).sum()),"max",d[:,:4].max().round(2),d[:,4:].max().round(1))
for n in ("human_M_idle_turn_90_left","human_M_idle_turn_90_right","human_M_Idle_Turn_180_Left","Human_M_Idle_Turn_180_Right","Human_Idle_turn_90_Left_Ent_Run","Human_Idle_turn_90_Right_Ent_Run","Human_Idle_turn_180_Right_Ent_Run","human_Run_Turn_180_Short","human_run_start_01","human_run_stop_01"):
    R,fps=load(n);rows=[]
    for j in (0,1,2):
        a=[math.degrees(math.atan2(*fwd(R[f,j,:4])[0][1::-1])) for f in range(len(R))]
        rows.append(np.unwrap(np.radians(a)).__mul__(57.3).round(0)[[0,len(a)//2,-1]].tolist())
    print(n,"x-axis yaw of j0,j1,j2 first/mid/last",rows,"t",R[-1,1,4:7].round(0).tolist())
