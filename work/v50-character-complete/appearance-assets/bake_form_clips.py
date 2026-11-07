import json,struct,subprocess,math,sys
from pathlib import Path
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[2];sys.path.insert(0,str(O));import asset_source as A
cat=json.loads((O/"appearance-source-catalogue.json").read_text());models={m["fab"]:m for m in cat["models"]}
groups=[(456813,103195,[703318,708356,702903,702904,708025,457557,457536,1576362]),(611642,666245,[1293793,1293889,1293982,1294014,1294118,656035,655636,1666387]),(1507280,1438362,[1576362]),(1507282,1438379,[1666387])]
ids=sorted({sid for _,_,ids in groups for sid in ids})
files=A.extract([f"{sid}.anm_bxml"for sid in ids]+[f"{sid}.mtns_bxml"for _,sid,_ in groups])
rows=[];links=[]
for rig,mset,ids in groups:
 sf=R/models[rig]["path"];fb=sf.read_bytes();ms=files[f"{mset}.mtns_bxml"];mb=ms.read_bytes()
 # For game Win_Face uses separatelinkedCharacterWindow MSet, actualPlayerMSet alsocarriesclip asset.
 for sid in ids:
  clip=files[f"{sid}.anm_bxml"];cb=clip.read_bytes();occ=[];o=0
  while(o:=mb.find(struct.pack("<I",sid),o))>=0:occ.append(o);o+=4
  assert occ,(rig,mset,sid)
  dst=O/f"clips/{rig}-{sid}.local-trs.bin"
  cmd=[str(R/"work/v20-char/clip-bake.exe"),str(R/"work/v30-engine/koa.exe"),str(sf),str(clip),str(dst)]
  z=subprocess.run(cmd,capture_output=True,text=True,timeout=60);assert z.returncode==0,(sid,z.stdout,z.stderr)
  b=dst.read_bytes();n,nf,fps=struct.unpack_from("<IIf",b);cj=struct.unpack_from("<H",cb,22)[0]
  assert n==64 and cj==64 and len(b)==12+n*nf*48
  v=list(struct.iter_unpack("<12f",b[12:]));assert all(math.isfinite(x)for r in v for x in r)
  rows.append(dict(form="CREATOR"if rig in[1507280,1507282]else"GAMEPLAY",rig=rig,motion_set=mset,motion_set_path=str(ms.relative_to(R)),motion_set_sha256=A.H(mb),clip=sid,source_clip_path=str(clip.relative_to(R)),source_clip_sha256=A.H(cb),source_rig_path=str(sf.relative_to(R)),source_rig_sha256=A.H(fb),motion_set_clip_offsets=occ,path=str(dst.relative_to(O)),bytes=len(b),sha256=A.H(b),joints=n,clip_joints=cj,frames=nf,fps=fps,scale_min=[min(r[8+k]for r in v)for k in range(3)],scale_max=[max(r[8+k]for r in v)for k in range(3)],command=cmd,stdout=z.stdout))
 # exact firstWinFace slot—counted dictionarythenfirstvariant directlynative00d47350/d42ad0
 if mset in[1438362,1438379]:
  n=struct.unpack_from("<I",mb)[0];keys=struct.unpack_from("<"+"I"*n,mb,4);at=4+4*n
  slots,variants,flag,clips=struct.unpack_from("<4I",mb,at);clip=struct.unpack_from("<I",mb,at+16)[0]
  assert keys[0]==9624060 and variants==1 and clips==1 and clip==ids[0]
  links.append(dict(rig=rig,motion_set=mset,key="Win_Face_Idle",key_hash=keys[0],key_index=0,slot_count=slots,variant_count=variants,variant_flag=flag,clip_count=clips,clip=clip,clip_file_offset=at+16))
receipt=dict(clips=rows,exact_first_slot_links=links,source_policy="Win_Face_Idle firstslot nativecountedsourcejoin is exact. Gameplaywalk/run/idle clips are actualboundPlayer/Player_F assetreferences andsex-ownrig64channeldecodes; completeMotionSetchooser/blend/eventrootmotion policy is not implemented.",no_borrowed_male_female_rigs=True)
(O/"form-clip-receipt.json").write_text(json.dumps(receipt,indent=2))
print(json.dumps([dict(rig=r["rig"],clip=r["clip"],frames=r["frames"],bytes=r["bytes"],scale_min=r["scale_min"],scale_max=r["scale_max"])for r in rows],indent=2))
