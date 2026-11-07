import json,struct,hashlib,collections,csv
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2]
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cat=json.loads((O/"appearance-source-catalogue.json").read_text());types={t["id"]:t for t in cat["types"]};models={m["fab"]:m for m in cat["models"]};build={m["fab"]:m for m in json.loads((O/"model-build-receipt.json").read_text())["models"]}
profiles=json.loads((O/"selection-source-receipt.json").read_text())["profiles"]
mats={m["material"]:m for m in json.loads((R/"work/v50-character-complete/materials/material-catalog.json").read_text())}
rows=[]
for pi,p in enumerate(profiles):
 for opt in cat["options"]:
  if not(opt["race_mask"]&p["race_bit"]and opt["gender_mask"]&p["sex_bit"]):continue
  t=types[opt["asset_id"]];rr=t.get("rendering",{});fab=rr.get("model_variants",[0,0,0])[0 if p["sex_bit"]==1 else 1]
  mids=sorted(set(e["native_material_id"]for e in models[fab]["elements"]))if fab else[]
  w=t.get("customization_item",{}).get("words",[0,0,0,0])
  rows.append(dict(profile=pi,profile_name=p["name"],category_hash=opt["category_hash"],simtype=opt["asset_id"],source_palette_offset=opt["file_offset"],condition_handle_raw=opt["condition_handle_raw"],race_mask=opt["race_mask"],sex_mask=opt["gender_mask"],selected_fab=fab,source_type_sha256=t["sha256"],model_sha256=H(O/build[fab]["path"])if fab else None,bones=build[fab]["bones"]if fab else 0,max_palette=build[fab]["max_palette"]if fab else 0,near_group=1,native_mids=mids,material_kinds=sorted(set(mats[mid]["kind"]for mid in mids if mid)),tattoo_texture=w[1]if opt["category_hash"]==1756520 else 0,raw_source_and_native_layout_verified=True,production_creator_and_gameplay_plan_pass=True,original_game_option_availability="shared native unconditional TRUE expression exact assetinfos-key association; see ../creation-gameplay/availability-audit",original_game_visual_comparison="not performed inthisscope",shader_policy="See materials/source-oracle-validation.json; environment/probe callerinput explicit"))
(O/"option-vetting-matrix.json").write_text(json.dumps(dict(unique_source_options=184,profile_option_rows=len(rows),rows=rows,scope="Every source mask-compatible mesh/tattoo option, bothforms. Source+CPUchecks do not claim originalUI/runtimeavailability/pixelparity."),indent=2))
with(O/"option-vetting-matrix.csv").open("w",newline="")as f:
 writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
native={}
for p in sorted((O/"native-evidence").glob("*.c")):native[p.name]=H(p)
payload=[*sorted((O/"models").glob("*.oaam")),*sorted((O/"clips").glob("*.local-trs.bin")),*[O/n for n in["oa_appearance.h","oa_appearance.c","oa_appearance_selection.h","oa_appearance_selection.c","oa_appearance_selection_data.h"]]]
manifest=dict(runtime_files=[dict(path=str(p.relative_to(O)),bytes=p.stat().st_size,sha256=H(p))for p in payload],total_runtime_bytes=sum(p.stat().st_size for p in payload),model_files=len(models),clip_files=len(list((O/"clips").glob("*.local-trs.bin"))),source_option_count=184,compatible_profile_option_rows=len(rows),native_executable_sha256="16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314",native_evidence=native,untouched="No live/default/frozenpreview/sourcearchives/DB/save files edited. Alltaskwrites isolatedhere.",format="OAAM001 chunkmodel +nativeEdge localQTS48 clips +C99selection/poseAPI",materials_owner="../materials/",source_receipts=["appearance-source-catalogue.json","model-build-receipt.json","independent-validation.json","creator-clip-receipt.json","form-clip-receipt.json","selection-source-receipt.json","option-vetting-matrix.json","production-loader-test.log","head-dependent-validation.log","../creation-gameplay/availability-audit/REPORT.md"])
(O/"delivery-manifest.json").write_text(json.dumps(manifest,indent=2))
print(json.dumps({k:v for k,v in manifest.items()if k not in["runtime_files","native_evidence"]},indent=2))
