import sys,json,struct,collections
from pathlib import Path
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent; R=O.parents[2]
for d in ["v15-properties","v13-properties","v07-bxml","v07-mesh","v45-foliage-coverage/instance-audit"]:sys.path.insert(0,str(R/"work"/d))
sys.path.insert(0,str(O))
import asset_source as A,native_type_catalog as C
from parse_authored_fab_groups import parse_fab_groups
N={r["kind"]:r["tables"][0]["name"] for r in json.loads((R/"outputs/scene-v13/component-map.json").read_text())["components"]}
batch=(R/"work/scene-inputs-v09/patch_0.pak/134225858_ksmt.batch").read_bytes();idx=C.index_batch(batch)
options=json.loads((R/"work/v49-character-create/analysis/source-customization-options.json").read_text())["records"]
for option in options: option["condition_handle_raw"]=option.pop("asset_type_raw")
refs=json.loads((R/"work/v49-character-create/analysis/default-asset-references.json").read_text())
creator={k:v["simtype"] for k,v in refs.items()}
gameplay={"Human_Male":669805,"Human_Female":669806,"Elf_Male":669807,"Elf_Female":669808}
def type_row(sid):
 raw=C.member_bytes(batch,idx["members"][sid]);d=C.decode_type(raw,N);out=dict(id=sid,sha256=A.H(raw),parent=d["parent_key_u32"],script=d["script_key_u32"],flags=d["type_flags_u32"],components=[])
 for c in d["components"]:
  at=8+c["payload_offset"]
  if c["kind"]==7:
   w=struct.unpack_from("<14I",raw,at)
   arr=lambda off,n,stride:[list(struct.unpack_from("<"+"I"*stride,raw,off+i*4*stride)) for i in range(n)]
   out["rendering"]=dict(blueprint_file_offset=at,primary_fab=w[5],model_variants=list(w[6:9]),mount_hash=w[11],scale=struct.unpack_from("<f",raw,at+48)[0],attachments=arr(w[1],w[2],2),slot_controls=[v[0] for v in arr(w[3],w[4],1)],raw_hex=raw[at:at+56].hex())
  elif c["kind"]==8:out["stats_identity"]=dict(blueprint_file_offset=at,race_raw=struct.unpack_from("<I",raw,at+4)[0],sex_raw=struct.unpack_from("<I",raw,at+8)[0])
  elif c["kind"]==40:out["customization_item"]=dict(file_offset=at,words=list(struct.unpack_from("<4I",raw,at)))
 return out
ids=sorted(set([r["asset_id"] for r in options]+list(creator.values())+list(gameplay.values())+[1321542,1321543,1330206,1330207,1381439]))
missing_types=[sid for sid in ids if sid not in idx['members']]
types={sid:type_row(sid) for sid in ids if sid in idx['members']}
fabs=set([1507280,1507282,456813,611642])
for v in types.values():
 r=v.get("rendering",{});fabs.update(x for x in [r.get("primary_fab",0),*r.get("model_variants",[])] if x);fabs.update(x[0] for x in r.get("attachments",[]) if x[0])
inputs=A.extract([f"{sid}.fab_bxml" for sid in fabs]+[f"{sid}.fab_visual_data_streamable_bin" for sid in fabs])
models=[];missing=[]
for sid in sorted(fabs):
 key=f"{sid}.fab_bxml"
 if key not in inputs:missing.append(dict(fab=sid,reason="FABmetadata absent archive lists"));continue
 try:g=parse_fab_groups(inputs[key])
 except Exception as e:missing.append(dict(fab=sid,reason="groupdecode "+repr(e)));continue
 models.append(dict(fab=sid,path=str(inputs[key].relative_to(R)),sha256=g["sha256"],stream=str(inputs.get(f"{sid}.fab_visual_data_streamable_bin","")),groups=g["groups"],elements=g["elements"]))
mids=sorted(set(e["native_material_id"] for m in models for e in m["elements"]))
deps=dict(material_ids=mids,model_count=len(models),missing_models=missing,models=[dict(fab=m["fab"],material_ids=sorted(set(e["native_material_id"] for e in m["elements"]))) for m in models])
(O/"material-dependencies.json").write_text(json.dumps(deps,indent=2))
catalogue=dict(schema=1,creator_types=creator,gameplay_types=gameplay,types=list(types.values()),options=options,models=models,unresolved_model_variant_selector=True,missing_types=missing_types,batch_sha256=idx["input_sha256"])
(O/"appearance-source-catalogue.json").write_text(json.dumps(catalogue,indent=2))
print(json.dumps(dict(types=len(types),options=len(options),fabs=len(fabs),models=len(models),missing=missing,mids=len(mids)),indent=2))
