import json
f='outputs/scene-v19/lighting-provenance.json';p=json.load(open(f))
p['binding']=[r for r in p['binding'] if not r['claim'].startswith(('Space links','Scene lighting does not'))]
p['binding']+=[
 {"claim":"Space root +0x34 holds the region asset id, resolved at render setup","status":"native_confirmed","consumer":"FUN_00fc6800","evidence":"943 of 950 spaces resolve to an extracted region id; 6 patch ids have no region file, 1 is zero, 1 file has another header"},
 {"claim":"Region root +0xE8 is passed to the environment manager as cubes, records and hours","status":"native_confirmed","consumer":"FUN_00fcb620, FUN_00ce21d0"},
 {"claim":"Each 0x570-byte record is converted to a 0x314-byte runtime entry holding a back-pointer at +0x310","status":"native_confirmed","consumer":"FUN_00ce21d0, FUN_00ccb310"},
 {"claim":"Region root +0x08 is the sky asset handle","status":"native_confirmed","consumer":"FUN_00fed630, FUN_00fb8780"},
 {"claim":"The 8-byte region key is not the scene binding","status":"asset_verified","evidence":"136 region files and 487 spaces carry an all-zero key"},
 {"claim":"Shop cube pixels are the same in DATA and patch for every key","status":"asset_verified","evidence":"Ambient resolves to one cube and character to another in both; only table size differs"}]
p['time']=[r for r in p['time'] if not r['claim'].startswith('How clock')]+[
 {"claim":"Region hours are copied to TimeOfDayLightingMgr +0x30 and compared against the clock; each key holds until its end hour, then blends to the next key","status":"native_confirmed","consumer":"FUN_00c49640, FUN_00c7c5e0, FUN_00c7c8f0"},
 {"claim":"Exact blend-factor formula in the transition","status":"hypothesis","evidence":"FUN_00c7c710 not decompiled"}]
p['constants']=[
 {"claim":"sunLightColor = rgb * hdr * directional_light_intensity","status":"native_confirmed","consumer":"FUN_00cd6680"},
 {"claim":"sunLightDirection = -directional_light_direction","status":"native_confirmed","consumer":"FUN_00cd6680"},
 {"claim":"shadowColor = (shadow_color.rgb, shadow_opacity)","status":"native_confirmed","consumer":"FUN_00cd6680; shader uses .w as shadow opacity"},
 {"claim":"worldToFogConstants.xy = (density/500000, fog_start), with fog scales applied through global weight +0xB8","status":"native_confirmed","consumer":"FUN_00c8a880, FUN_00cd6680"},
 {"claim":"Fog color is blended toward a luminance value by min(environment_max, weight)","status":"native_confirmed","consumer":"FUN_00cd6680"},
 {"claim":"environmentTint and skyLightColor are copied unchanged","status":"native_confirmed","consumer":"FUN_00cd6680"},
 {"claim":"Bloom and DOF values are copied, with DOF ranges clamped to be ordered","status":"native_confirmed","consumer":"FUN_00cd6b70"},
 {"claim":"Packet 0x40 fields reach g_globalbuffer under these names","status":"hypothesis","evidence":"Packet stored by FUN_00c90970; the final constant-buffer write was not traced. Field meanings fit the shader use"}]
p['unresolved']=[
 "Final write from packet 0x40 state to g_globalbuffer",
 "Value of global weight +0xB8 during normal play; when 0, luminance_shift scales have no effect on fog or bloom",
 "luminance_shift.bxml name-to-value alignment; hashes match the reader but the table order is not yet decoded",
 "How environment_tint is used in the shaders that read it; ambientDiffuseScale, ambientSpecularScale and backlightScale values",
 "Record +0x000..+0x23F is not read by FUN_00ccb310; other readers unknown",
 "Meaning of flags bit 0 in the renderer; shadow policy; active shadowapply variant",
 "sky_bxml field layout (four 0x30 key groups and texture slots seen in FUN_00fbb2c0); color-correction texture decode; cube channel and face order",
 "Forward light selection; files 587658.region_bxml and 587656.space_bxml; six patch spaces whose region id has no file"]
p['capture_questions']=[
 {"question":"Read g_globalbuffer, including ambient and backlight scales and global weight, while any lit scene renders","requires":"Any representative loaded scene, not the shop"},
 {"question":"Compare final image for the shop","requires":"Shop loaded; only for that validation"}]
json.dump(p,open(f,'w'),indent=1)
