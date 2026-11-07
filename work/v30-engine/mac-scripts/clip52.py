import json,struct
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur"
b=(root/"work/v20-char/character.bin").read_bytes();J,C,_,_=struct.unpack_from("<IIII",b,8);o=24;par=struct.unpack_from(f"<{J}h",b,o);o+=J*2
clips=[]
for c in range(C):
    fr,fps=struct.unpack_from("<If",b,o);o+=8;clips.append((fr,fps,np.frombuffer(b,"<f4",fr*J*7,o).reshape(fr,J,7)));o+=fr*J*28
labels=["idle","walk","run","x01","xx01","xxx01","react","death","sw_idle","sw_walk","sw_run","xxxx01","x02","xx02","xxx02","xxxx02"]
ref=clips[0][2][0]
for c,l in enumerate(labels):
    fr,fps,A=clips[c]
    ang=lambda j:np.degrees(2*np.arccos(np.clip(np.abs((A[:,j,:4]*ref[j,:4]).sum(1)),0,1)))
    t=np.linalg.norm(A[:,:,4:]-ref[:,4:],axis=2)
    print(l,"frames",fr,"root0 t",np.round(A[0,0,4:],1).tolist(),"root1 t f0",np.round(A[0,1,4:],0).tolist(),"root1 t mid",np.round(A[fr//2,1,4:],0).tolist(),"pelvis t",np.round(A[0,2,4:],1).tolist(),"worst bone stretch",round(float(t[:,3:].max()),1),"at joint",int(np.unravel_index(t[:,3:].argmax(),t[:,3:].shape)[1])+3,"pelvis rot deg",round(float(ang(2).max())),"root1 rot",round(float(ang(1).max())))
print("x01 joint lengths vs idle at f0: joints whose bone length changed",[j for j in range(52) if abs(np.linalg.norm(clips[3][2][0,j,4:])-np.linalg.norm(ref[j,4:]))>.5][:30])
print("xx01 same",[j for j in range(64) if abs(np.linalg.norm(clips[4][2][0,j,4:])-np.linalg.norm(ref[j,4:]))>.5][:30])
