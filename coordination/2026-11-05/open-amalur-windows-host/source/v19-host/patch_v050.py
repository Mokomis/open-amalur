import re,shutil
from pathlib import Path
R=Path.home()/"Documents/Opem Amalur";W=R/"work/v20-char";H=R/"work/v19-host"
def edit(f,fn):
    s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n");s=fn(s)
    if crlf:s=s.replace("\n","\r\n")
    f.write_bytes(s.encode())
def rep(s,a,b):
    assert a in s,a[:70]
    return s.replace(a,b,1)
def town(s):
    s=rep(s,'masks = pickle.load(open(root / "work/v20-char/terrain-masks.pkl", "rb"))\n','')
    s=rep(s,'grids = pickle.load(open(wc / "terrain-grids.pkl", "rb"))','terrain_dir = Path(__import__("os").environ.get("OA_TERRAIN_DIR", str(root / "work/v24-zones/dal")))\nmasks = pickle.load(open(terrain_dir / "terrain-masks.pkl", "rb"))\ngrids = pickle.load(open(terrain_dir / "terrain-grids.pkl", "rb"))')
    s=rep(s,'abs_pos = pickle.load(open(wc / "terrain-abs.pkl", "rb"))','abs_pos = pickle.load(open(terrain_dir / "terrain-abs.pkl", "rb"))')
    s=rep(s,'fit = json.loads((wc / "terrain-fit.json").read_text())','fit = json.loads((terrain_dir / "terrain-fit.json").read_text())')
    s=rep(s,'SPACE, REGION, DOOR = 431638, 431608, (1575.1, -62759.2, 5152.1)','SPACE, REGION, DOOR = 431638, int(__import__("os").environ.get("OA_REGION", 431608)), (1575.1, -62759.2, 5152.1)')
    return s
edit(W/"build_town.py",town)
def zone(s):
    s=rep(s,'spaces = sorted((int(k), str(v)) for k, v in syms["simspace"].items() if re.match(r"out_dal_(north|south|west|tran)_", str(v)))','ZONE = __import__("os").environ.get("OA_ZONE", "dal")\nspaces = sorted((int(k), str(v)) for k, v in syms["simspace"].items() if re.match(rf"out_{ZONE}_(north|south|west|east|central|tran|[a-z0-9])", str(v)))')
    return s
edit(W/"build_zone.py",zone)
def veg(s):
    s=rep(s,'import collections,json,pickle,struct,sys,zlib\n','import collections,json,os,pickle,struct,sys,zlib\n')
    s=rep(s,'out=root/"work/v22-stress/zone-dal";out.mkdir(parents=True,exist_ok=True)','out=Path(os.environ.get("OA_ZONE_DIR",str(root/"work/v22-stress/zone-dal")));out.mkdir(parents=True,exist_ok=True);tdir=Path(os.environ.get("OA_TERRAIN_DIR",str(root/"work/v24-zones/dal")));tid=os.environ.get("OA_TERRAIN_ID","431658")')
    s=rep(s,'vb=(inp/"DATA_0.pak/431658.veggie_streamable_bin").read_bytes()','import subprocess\ng=Path(r"C:\\Program Files (x86)\\Steam\\steamapps\\common\\Kingdoms of Amalur Re-Reckoning")\nif not (inp/f"DATA_0.pak/{tid}.veggie_streamable_bin").exists():subprocess.run([str(g/"modding/pakfileunpacker.exe"),str(g/"data/DATA_0.pak"),"unpack",str(inp/"DATA_0.pak"),f"{tid}.veggie_streamable_bin"],cwd=g/"modding",capture_output=True,timeout=280)\nvb=(inp/f"DATA_0.pak/{tid}.veggie_streamable_bin").read_bytes()')
    s=rep(s,'grids=pickle.load(open(wc/"terrain-grids.pkl","rb"));masks=pickle.load(open(wc/"terrain-masks.pkl","rb"));abs_pos=pickle.load(open(wc/"terrain-abs.pkl","rb"));fit=json.loads((wc/"terrain-fit.json").read_text())','grids=pickle.load(open(tdir/"terrain-grids.pkl","rb"));masks=pickle.load(open(tdir/"terrain-masks.pkl","rb"));abs_pos=pickle.load(open(tdir/"terrain-abs.pkl","rb"));fit=json.loads((tdir/"terrain-fit.json").read_text())')
    return s
edit(W/"build_veggie.py",veg)
def cut(s):
    s=rep(s,'z=root/"work/v22-stress/zone-dal";pk=root/"work/v22-stress/live-pack";','z=Path(__import__("os").environ.get("OA_ZONE_DIR",str(root/"work/v22-stress/zone-dal")));')
    return s
edit(W/"build_cutoffs.py",cut)
def act(s):
    s=rep(s,'OUT = root / "work/v23-actors"; OUT.mkdir(parents=True, exist_ok=True)','OUT = Path(__import__("os").environ.get("OA_ACTORS_DIR", str(root / "work/v23-actors"))); OUT.mkdir(parents=True, exist_ok=True)\nZONE = __import__("os").environ.get("OA_ZONE", "dal")')
    s=rep(s,'if re.match(r"out_dal_(north|south|west|tran)_", str(v))}','if re.match(rf"out_{ZONE}_", str(v))}')
    return s
edit(W/"build_actors.py",act)
def route(s):
    s=rep(s,'z=root/"work/v22-stress/zone-dal";out=root/"work/v23-actors"','import os\nz=Path(os.environ.get("OA_ZONE_DIR",str(root/"work/v22-stress/zone-dal")));out=Path(os.environ.get("OA_ACTORS_DIR",str(root/"work/v23-actors")))')
    s=rep(s,'door=(1575.1,-62759.2);','door=tuple(float(x) for x in os.environ.get("OA_START","1575.1 -62759.2").split());')
    return s
edit(W/"build_route.py",route)
def pack(s):
    s=rep(s,"for _p in (root/'work/v23-actors').glob('*.bin'):","for _p in Path(_os.environ.get('OA_ACTORS_DIR',str(root/'work/v23-actors'))).glob('*.bin'):")
    return s
edit(H/"package_android.py",pack)
(R/"work/v24-zones/dal").mkdir(parents=True,exist_ok=True)
for n in ("terrain-grids.pkl","terrain-abs.pkl","terrain-masks.pkl","terrain-fit.json"):shutil.copy(R/"work/v24-zones/dal-check"/n,R/"work/v24-zones/dal"/n)
print("ok")
