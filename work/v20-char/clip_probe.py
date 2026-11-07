import json,math,struct,subprocess,sys,re
from pathlib import Path
import numpy as np
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
g=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning");out=root/"work/v20-char";inp=root/"work/v20-inputs"
A={v:int(k) for k,v in syms["animation"].items()}
names="""human_idle_01 Player_Idle Player_Idle_Variation01 human_walk_01 human_walk_02 human_walk_03 human_Jog_01 human_Jog_02 human_run_01 human_run_02 human_run_03 human_sprint_01 human_sprint_start human_Sprint_stop_01
human_run_start_01 human_Jog_Start_01 human_run_stop_01 human_run_stop_short_01 human_M_walk_Start human_M_walk_stop human_M_walk_stop_L human_M_walk_stop_R
human_M_idle_turn_90_left human_M_idle_turn_90_right human_M_Idle_Turn_180_Left Human_M_Idle_Turn_180_Right human_M_Idle_Turn_90_Left_walk human_M_Idle_Turn_90_Rgt_walk Human_Idle_turn_90_Left_Ent_Run Human_Idle_turn_90_Right_Ent_Run Human_Idle_turn_180_Right_Ent_Run human_Run_Turn_180_Short human_Run_TurnRightBack
human_run_Slope_Up_Blend human_run_Slope_Down_Blend human_run_turn_left_Blend human_run_turn_Right_Blend human_sprint_turn_Left_Blend human_sprint_turn_Right_Blend human_additive_zero human_Armor_Blend
human_roll_frt human_roll_frt_short human_sword_putaway_01 human_sword_attack_dash human_sword_special_block human_sword_attack_special human_jump_fall_Idle human_jump_hard_land""".split()
extract([f"{A[n]}.anm_bxml" for n in names if n in A])
def yaw(q): return math.degrees(2*math.atan2(q[2],q[3]))
for n in names:
    if n not in A: print(n,"NO NAME");continue
    cid=A[n];f=None
    for pak in ("patch_0.pak","initial_0.pak","DATA_0.pak"):
        q=inp/pak/f"{cid}.anm_bxml"
        if q.exists(): f=q;break
    if not f: print(n,"no file");continue
    d=f.read_bytes();nj=struct.unpack_from("<H",d,8+0xe)[0];baked=out/f"baked/{cid}.bin"
    if not baked.exists():
        r=subprocess.run([str(out/"clip-bake.exe"),str(g/"koa.exe"),str(inp/"patch_0.pak/456813.fab_bxml"),str(f),str(baked)],capture_output=True,text=True)
        if r.returncode: print(n,cid,f.parent.name,"joints",nj,"BAKE FAIL",r.stderr[:80]);continue
    b=baked.read_bytes();j,fr,fps=struct.unpack_from("<IIf",b)
    R=np.frombuffer(b,"<f4",offset=12).reshape(fr*j,12)[:,:7].reshape(fr,j,7)
    # q conj as in build_character
    root=R[:,0,:];hip=R[:,1,:] if j>1 else root
    dt=root[-1,4:7]-root[0,4:7];dh=hip[-1,4:7]-hip[0,4:7]
    yq0=np.array([-root[0,0],-root[0,1],-root[0,2],root[0,3]]);yq1=np.array([-root[-1,0],-root[-1,1],-root[-1,2],root[-1,3]])
    rng=np.abs(R[:,:,:4]-R[0,:,:4]).max()
    print(f"{n:38s} id {cid} {f.parent.name[:7]} j {nj}/{j} fr {fr} fps {fps:.0f} sec {fr/fps:.2f} root d {dt.round(0).tolist()} yaw {yaw(yq0):.0f}>{yaw(yq1):.0f} hip d {dh.round(0).tolist()} rot range {rng:.2f}")
