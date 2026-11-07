import json,sys,hashlib,struct,glob,os
sys.path.insert(0,'work/v19-lighting')
import decode_scene_lighting as D
OUT='outputs/scene-v19/'
b=open('work/v19-inputs/DATA_0.pak/587658.region_bxml','rb').read()
print('587658 head',b[:32].hex(),'inner',struct.unpack_from('<II',b,8))
print('patch has 587658',os.path.exists('work/v19-inputs/patch_0.pak/587658.region_bxml'))
prov={
"schema":D.SCHEMA,"statuses":D.STATUS,
"target_sha256":"16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314",
"binding":[
 {"claim":"A region_bxml embeds one compiled environment record through root slot 0xF0","status":"asset_verified","evidence":"883 of 884 region files decode; the remaining file has a different container header"},
 {"claim":"Scene lighting does not reference a koalighting file at runtime by name","status":"hypothesis","evidence":"No name or asset reference appears in the record; authored values are compiled in. Native load path not fully traced"},
 {"claim":"Record cube indices at +0x550 and +0x560 select per-key ambient cubes in a 0x30-stride table","status":"native_confirmed","consumer":"FUN_00cadf30"},
 {"claim":"Space links to region by 8-byte key at space root +0x48 and region root +0","status":"asset_verified","evidence":"799 of 950 decodable spaces match a region key in the extracted corpus; 151 do not and remain unexplained"},
 {"claim":"Shop region 524912 compiled values equal lighting_int_dal_gorhartinn_region","status":"asset_verified","evidence":"All compared fields plus direction match; no other shipped preset matches. This is value equality, not a stored name"}],
"time":[
 {"claim":"Four keys ordered Midnight, Dawn, Noon, Dusk","status":"asset_verified"},
 {"claim":"Two keys blend linearly by state {a,b,t,flag} in TimeOfDayLightingMgr +0xC","status":"native_confirmed","consumer":"FUN_00c8a160, FUN_00c49860"},
 {"claim":"Region day-division hours are authored at root +0xF8","status":"asset_verified"},
 {"claim":"How clock hours produce {a,b,t}","status":"hypothesis","evidence":"Not traced"}],
"blending":[
 {"claim":"Environment contributors accumulate by weight, with the remainder filled by the base environment and then normalized","status":"native_confirmed","consumer":"FUN_00df6150, FUN_00c37290, FUN_00e170b0, FUN_00c37500"},
 {"claim":"Contributor weight is (1-saturate(distance/fade))*base","status":"native_confirmed","consumer":"FUN_00df6150"}],
"global_defaults":[
 {"claim":"luminance_shift.bxml supplies tint, luminance, scale and max terms for character, environment and sky, plus fog and bloom scales","status":"native_confirmed","consumer":"FUN_00c62d30"},
 {"claim":"Bloom exposure, min, max and strength are scaled by those globals through a weight","status":"native_confirmed","consumer":"FUN_00cd6b70"},
 {"claim":"Values inside luminance_shift.bxml","status":"unmapped","evidence":"File identified, not yet decoded"}],
"point_lights":[
 {"claim":"Color = rgb * hdr intensity * multiplier; scale = -1/(end-start); bias = end/(end-start); start treated as 0 if end <= start","status":"native_confirmed","consumer":"FUN_00ccf660"},
 {"claim":"Attenuation = saturate(distance*scale+bias)","status":"shader_confirmed","consumer":"forward PS loop and rspointlightsheet PS"},
 {"claim":"Forward materials evaluate at most 4 point lights per draw","status":"shader_confirmed","evidence":"g_forwardLighting constants[8] and loop bound 4"},
 {"claim":"Forward light selection policy","status":"hypothesis","evidence":"Not traced"},
 {"claim":"Space source record field order maps to the runtime Light fields","status":"hypothesis","evidence":"Offsets fit the 4-key layout and getters, but the copy from source to runtime was not traced"}],
"shaders":[
 {"claim":"G-buffer: o0 normal and gloss; o1 albedo and specular; o2 ambient = (1-specScale)*cube(N)*albedo + sky specular term","status":"shader_confirmed"},
 {"claim":"Deferred combine: (shadowColor*(1-sunTerm)*albedo + gbuffer ambient)*ssao + (sun+lightBuffer)*albedo + specular","status":"shader_confirmed"},
 {"claim":"Shadow strength uses shadowColor.w as 1+w*(shadow-1)","status":"shader_confirmed"},
 {"claim":"Fog factor = min(1, 2^-(a*z+b)) from worldToFogConstants","status":"shader_confirmed"},
 {"claim":"Color correction blends four 3D LUTs, then applies brightness gamma and color transition","status":"shader_confirmed"},
 {"claim":"Final combine applies a 2D correction lookup","status":"shader_confirmed"}],
"unresolved":[
 "Mapping from the 0x570 region record to the 0x314 runtime struct read by FUN_00c8a160; offsets differ from the record",
 "How fog_start and fog_density derive worldToFogConstants",
 "Whether sunLightColor equals directional_light_color*intensity, and how environment_tint and particle_tint reach shaders",
 "Record +0x000..+0x23F is not in authored XML; bytes preserved as unmapped",
 "flags field location and meaning; directional shadow policy; which shadowapply variant is active",
 "luminance_shift.bxml values; sky_bxml format; color-correction texture decode; ambient cube channel order",
 "DATA versus patch precedence for the same region id; shop has differing cube tables",
 "Files 587658.region_bxml and 587656.space_bxml use a different header"],
"capture_questions":[
 {"question":"Read g_globalbuffer while any lit scene renders, to resolve fog, sun and tint derivation","requires":"Any representative loaded scene, not the shop"},
 {"question":"Confirm patch versus DATA record selection","requires":"Any region with differing variants"},
 {"question":"Compare final image for the shop","requires":"Shop loaded; only for that validation"}]}
json.dump(prov,open(OUT+'lighting-provenance.json','w'),indent=1)
schema={"schema":D.SCHEMA,"statuses":D.STATUS,"keys":D.KEYS,"region":{"root":{"region_key":"+0x00 u8[8]","sky_asset_id":"+0x08 u32 (hypothesis)","ambient_cubes":"+0xE8 ptr,count; entry 0x30 = six ptr,64 faces of 8x8x4","environment":"+0xF0 ptr,count=1","day_division_hours":"+0xF8 float[8]: starts then ends"},"environment_record_bytes":D.ENV_RECORD_BYTES,"fields":[dict(name=n,offset=o,kind=k) for n,o,k in D.ENV_FIELDS]+[dict(name="directional_light_direction",offset=0x430,kind="float3")],"unmapped":D.ENV_UNMAPPED},"space":{"region_key":"+0x48 u8[8]","lights":"+0x90 ptr,count; stride 108: pos[3], color[4][3], multiplier[4], start[4], end[4]"}}
json.dump(schema,open(OUT+'scene-lighting-schema.json','w'),indent=1)
samples={'interior-shop':'work/v19-inputs/DATA_0.pak/524912.region_bxml'}
v=json.load(open(OUT+'decoder-validation.json'))
rv={}
for k,n in v['region_to_preset'].items():rv.setdefault(n,k)
for label,pat in (('exterior','lighting_out_dalentarth_region_old.koalighting'),('dungeon','lighting_dgn_eru_default.koalighting')):
    k=rv.get(pat)
    print(label,pat,k)
    if k:
        a,f=k.split('/');samples[label]=f'work/v19-inputs/{a}_0.pak/{f}' if not a.endswith('.pak') else f'work/v19-inputs/{a}/{f}'
os.makedirs(OUT+'decoded-samples',exist_ok=True)
for l,p in samples.items():
    if os.path.exists(p):open(OUT+f'decoded-samples/{l}.json','w').write(json.dumps(D.decode_region(open(p,'rb').read()),indent=0));print('sample',l,p)
    else:print('missing',p)
open(OUT+'decoded-samples/interior-shop-lights.json','w').write(json.dumps(D.decode_space_lights(open('work/scene-inputs-v07/DATA_0.pak/524859.space_bxml','rb').read()),indent=0))
progress="""Open Amalur V19 shared lighting recovery, 2026-10-31. Static analysis only; no game launch, build, install or device action.

RESULT: Lighting does not need a save or a loaded scene to decode. Each region_bxml embeds its compiled environment settings, ambient cubes and day-division hours. work/v19-lighting/decode_scene_lighting.py decodes them from bytes with per-field provenance.

CORRECTION TO V18: The Gorhart Inn preset was recorded as a related sample only. Shop region 524912 compiled values and direction equal lighting_int_dal_gorhartinn_region, and no other shipped preset matches. This is value equality; the record stores no preset name. Region key 8f028bbe0c91181c is the link between space and region, not a preset key.
V18 linear falloff is confirmed as the native form, not merely authored: saturate((end-d)/(end-start)). V18 ambient 0.12 is still a placeholder and should be replaced by the region cube, shadow color and G-buffer terms.

VALIDATION: 883 of 884 region files decode. 860 match a shipped preset on every compared field plus direction, using 94 presets. 23 do not match any single preset fully (mostly patch-only ids); listed in decoder-validation.json. Cube indices were in range for all 7064 values. 799 of 950 decodable spaces match a region key; 151 do not and are unexplained. Tests: work/v19-lighting/test_lighting.py.

SHADERS: 1095 embedded aPLib-packed DXBC blobs in koa.exe, 440 unique, all disassembled with D3DCompiler_47 into outputs/scene-v19/shaders. Blob-to-name mapping is by reflection and role, not a traced table.

NOT DONE: Android host integration. Native equivalence is not claimed. See lighting-provenance.json for confirmed claims, hypotheses, unresolved items and the selective capture questions.
"""
open(OUT+'PROGRESS.txt','w').write(progress)
json.dump({"stage":"v19-shared-lighting","status":"decoder-and-provenance-delivered","android_version_unchanged":"0.14.0","regions_decoded":883,"regions_total":884,"exact_preset_matches":860,"unique_shaders":440,"native_lighting_parity_verified":False,"game_launched":False,"apk_built":False,"device_touched":False,"blockers":prov['unresolved']},open(OUT+'continuation.json','w'),indent=1)
with open('work/CURRENT_STATE.txt','a',encoding='utf-8') as f:f.write('\n\nV19 SHARED LIGHTING RECOVERY (latest): static only, no build/install/game launch. See outputs/scene-v19/PROGRESS.txt, lighting-provenance.json, scene-lighting-schema.json; decoder work/v19-lighting/decode_scene_lighting.py. Region files embed compiled environment settings; a save is not required to decode. Do not claim native parity.\n')
