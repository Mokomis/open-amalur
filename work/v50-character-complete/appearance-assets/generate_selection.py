import json
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
cat=json.loads((O/"appearance-source-catalogue.json").read_text());types={t["id"]:t for t in cat["types"]}
old=json.loads((R/"work/v49-character-create/staged-source/creation-source-catalogue.json").read_text())["types"]
cats=[701554,481813,1139995,771605,1756520,9441502];keys=["Head","Hair","Beard","Ears","Tattoo","FaceAccesory"]
races={"Almain":64,"Varani":128,"Ljosalfar":512,"Dokkalfar":1024}
profiles=[];base=[];opts=[];equip=[]
for v in old:
 name=v["type"];sex=1 if v["gender"]=="Male"else 2;rb=races[v["race"]];defaults=[]
 for k,c in zip(keys,cats):
  sid=v["default_customization"].get(k,0)
  if not sid:
   sid=next((r["asset_id"]for r in cat["options"]if r["category_hash"]==c and r["race_mask"]&rb and r["gender_mask"]&sex),0)
  defaults.append(sid)
 ct=v["creator_simtype"];gt=v["full_player_simtype"];cr=types[ct]["rendering"];gr=types[gt]["rendering"]
 assert types[ct]["stats_identity"]["sex_raw"]==sex-1
 row=dict(name=name,race_bit=rb,sex_bit=sex,creator_type=ct,gameplay_type=gt,creator_fab=cr["primary_fab"],gameplay_fab=gr["primary_fab"],default_options=defaults,creator_idle_clip=703318 if sex==1 else 1293793,creator_face_idle_clip=1576362 if sex==1 else 1666387,gameplay_idle_clip=703318 if sex==1 else 1293793,gameplay_walk_clip=457557 if sex==1 else 656035,gameplay_run_clip=457536 if sex==1 else 655636)
 profiles.append(row);base.append([cr["attachments"],gr["attachments"]])
for r in cat["options"]:
 t=types[r["asset_id"]];rr=t.get("rendering",{});w=t.get("customization_item",{}).get("words",[0,0,0,0])
 opts.append(dict(simtype=r["asset_id"],category_hash=r["category_hash"],race_mask=r["race_mask"],sex_mask=r["gender_mask"],model_variants=rr.get("model_variants",[0,0,0]),mount_hash=rr.get("mount_hash",0),tattoo_texture=w[1] if r["category_hash"]==1756520 else 0))
for sid in [1321542,1321543,1330206,1330207,1381439]:
 r=types[sid]["rendering"];equip.append(dict(simtype=sid,model_variants=r["model_variants"],mount_hash=r["mount_hash"],scale=r["scale"]))
def ul(a):return ",".join(str(x)+"u"for x in a)
s="/* Generated from immutable original Type/palette/script records; see source catalogue. */\n"
s+="static const oa_ap_profile profiles[]={\n"
for r in profiles:s+='{"%s",%s,{%s},%s},\n'%(r["name"],ul([r[k]for k in ["race_bit","sex_bit","creator_type","gameplay_type","creator_fab","gameplay_fab"]]),ul(r["default_options"]),ul([r[k]for k in ["creator_idle_clip","creator_face_idle_clip","gameplay_idle_clip","gameplay_walk_clip","gameplay_run_clip"]]))
s+="};\nstatic const oa_ap_option options[]={\n"
for r in opts:s+="{%s,{%s},%su,%su},\n"%(ul([r[k]for k in ["simtype","category_hash","race_mask","sex_mask"]]),ul(r["model_variants"]),r["mount_hash"],r["tattoo_texture"])
s+="};\ntypedef struct {uint32_t fab,slot;} base_pair;\n"
for pi,forms in enumerate(base):
 for fi,rows in enumerate(forms):
  s+="static const base_pair base_%d_%d[]={%s};\n"%(pi,fi,",".join("{%su,%su}"%(a,b)for a,b in rows))
s+="static const base_pair *const bases[][2]={"+",".join("{base_%d_0,base_%d_1}"%(i,i)for i in range(8))+"};\n"
s+="static const uint32_t base_counts[][2]={"+",".join("{%s}"%ul([len(v)for v in forms])for forms in base)+"};\n"
s+="typedef struct{uint32_t sim,fab[3],mount;float scale;} equip_row;\nstatic const equip_row equipment[]={\n"
for e in equip:s+="{%su,{%s},%su,%.9gf},\n"%(e["simtype"],ul(e["model_variants"]),e["mount_hash"],e["scale"])
s+="};\n";s=s.replace(",1f}",",1.0f}")
(O/"oa_appearance_selection_data.h").write_text(s)
(O/"selection-source-receipt.json").write_text(json.dumps(dict(profiles=profiles,options=opts,equipment=equip,base_attachments=base,native_route="00f10660: primaryalias rootfirst,headfallback;00ccd2c0: explicitparent/childmap +unmatchedsourcehierarchy. Hidden Ears absentdefault=firstsourcefilteredoption sourceinit, not0."),indent=2))
print("generated",len(profiles),len(opts),len(equip))
