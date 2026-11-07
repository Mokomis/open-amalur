"""Pack the game's own sounds for Dalentarth: work/v23-audio/index.bin plus one s<n>.bin per sound (the original .ksdf bytes).
Real: the sounds, in their original MS ADPCM. Authored: which sound plays on which game event, because the motion tables' sound events are not decoded."""
import collections,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
OUT=root/"work/v23-audio";OUT.mkdir(parents=True,exist_ok=True)
for p in OUT.glob("*.bin"):p.unlink()
K=sorted({x for L in listing.values() for x in L if x.endswith(".ksdf")})
by=collections.defaultdict(list)
for x in K:by[x.split("__")[0]].append(x)
foot=by["collision_footstep_player"];print("footstep names",[x.split("__")[1] for x in foot][:90])
G={"bed_forest":by["ambient_forest_lp"],"pos_forest":by["ambient_pos_forest"],"water":by["ambient_pos_water_lp"],
 "foot_grass":[x for x in foot if re.search("grass|dirt|leaf|forest",x,re.I)] or foot,"foot_stone":[x for x in foot if re.search("stone|rock",x,re.I)] or foot,
 "blade_use":by["collision_weapons_use_blade"],"blade_hit":by["collision_weapons_impact_blade"]+by["collision_weapons_impact_flesh"],"bodyfall":by["collision_bodyfall"],"player_die":by["motion_player_die"]}
for nm,bank in (("wolf","motion_wolf"),("bear","motion_bear"),("boggart","motion_boggart"),("troll","motion_troll"),("sprite","motion_sprite"),("brownie","motion_brownie"),("ettin","motion_ettin"),("giantspider","motion_giant_spider"),("spider","motion_spider"),("giantrat","motion_giant_rat"),("barghest","motion_barghest"),("thresh","motion_thresh"),("kobold","motion_kobold"),("murghan","motion_murghan"),("jottun","motion_jottun"),("antelope","motion_antelope"),("niskaru","motion_niskaru"),("bandit","motion_human_npc"),("human","motion_human_npc"),("fear","motion_faergorta")):
    s=by.get(bank,[])
    if s:G[nm]=s
    else:print("no bank for",nm,[b for b in by if nm in b][:6])
index=bytearray(b"OAAU");rows=[];files={};total=0;bad=collections.Counter()
for name,names in G.items():
    got=extract(names);ids=[]
    for n in names:
        p=got.get(n)
        if not p:bad["missing"]+=1;continue
        if n in files:ids.append(files[n]);continue
        b=p.read_bytes()
        if b[:4]!=b"FORK":bad["no fork"]+=1;continue
        tag,chs,rate=struct.unpack_from("<HHI",b,0x2c)
        if tag!=2 or chs not in (1,2) or not 8000<=rate<=96000:bad[f"format {tag}"]+=1;continue
        i=len(files);files[n]=i;(OUT/f"s{i}.bin").write_bytes(b);total+=len(b);ids.append(i)
    rows.append((name,ids));print(name,len(ids))
index+=struct.pack("<II",len(rows),len(files))
for name,ids in rows:
    index+=struct.pack("<24sI",name.encode()[:23],len(ids))+struct.pack(f"<{len(ids)}I",*ids)
(OUT/"index.bin").write_bytes(bytes(index));print("sounds",len(files),"MB",round(total/1e6,1),"rejected",bad)
first=next(iter(files));print("reference",first,files[first])
