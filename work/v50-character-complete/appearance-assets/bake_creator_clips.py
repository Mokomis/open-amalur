import sys,json,struct,subprocess,hashlib,math,time
from pathlib import Path
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[2];sys.path.insert(0,str(O));import asset_source as A
D=O/"clips";D.mkdir(exist_ok=True)
groups=[(1507280,1507283,[703318,708356,702903,702904,708025]),(1507282,1507295,[1293793,1293889,1293982,1294014,1294118])]
files=A.extract([f"{s}.anm_bxml" for _,_,ids in groups for s in ids])
exe=R/"work/v20-char/clip-bake.exe";pe=R/"work/v30-engine/koa.exe"
assert A.H(exe.read_bytes())=="aa597dd00fcf06dcdaf1cb5755fdc5a7383b71f1ff684d9e4ddf976cd4b33d58"
assert A.H(pe.read_bytes())=="16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314"
rows=[]
for rig,mset,ids in groups:
 source=O/f"source/initial_0.pak/{rig}.fab_bxml";sk=source.read_bytes()
 for sid in ids:
  anm=files[f"{sid}.anm_bxml"];ab=anm.read_bytes();clipj=struct.unpack_from("<H",ab,8+14)[0]
  dst=D/f"{rig}-{sid}.local-trs.bin";cmd=[str(exe),str(pe),str(source),str(anm),str(dst)]
  z=subprocess.run(cmd,capture_output=True,text=True,timeout=60)
  assert z.returncode==0,(sid,z.stdout,z.stderr)
  b=dst.read_bytes();j,n,fps=struct.unpack_from("<IIf",b);assert len(b)==12+j*n*48 and j==64
  vals=list(struct.iter_unpack("<12f",b[12:]));assert all(math.isfinite(v) for row in vals for v in row)
  scales=[row[8:11] for row in vals];qnorm=[sum(v*v for v in row[:4]) for row in vals]
  rows.append(dict(rig=rig,motion_set=mset,clip=sid,source_clip=str(anm.relative_to(R)),source_clip_sha256=A.H(ab),source_rig_sha256=A.H(sk),source_clip_joints=clipj,joints=j,frames=n,fps=fps,path=str(dst.relative_to(O)),bytes=len(b),sha256=A.H(b),scale_min=[min(s[k] for s in scales) for k in range(3)],scale_max=[max(s[k] for s in scales) for k in range(3)],q_norm2_min=min(qnorm),q_norm2_max=max(qnorm),command=cmd,stdout=z.stdout,stderr=z.stderr))
(O/"creator-clip-receipt.json").write_text(json.dumps(dict(native_decoder="0111bf10",harness_sha256=A.H(exe.read_bytes()),clips=rows,selection_policy="Source-linked creator idle variants retained; deterministic clip0 preview policy, not claim native random chooser timing. RigTrack order is source skeleton index, unmapped suffix retains source bind.",quaternion="Raw Edge XYZW; conjugate exactly once in world-matrix conversion. Source Q/T/S order; no normalize."),indent=2))
print(json.dumps([{k:r[k] for k in ["rig","clip","source_clip_joints","frames","fps","scale_min","scale_max"]} for r in rows],indent=2))
