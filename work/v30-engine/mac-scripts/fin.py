import json,hashlib
p='work/v19-lighting/lighting_model.py';s=open(p,encoding='utf-8').read()
s+='''

def key_transition(clock_hours, end_a, start_b):
    """native_confirmed: FUN_00c7c710 gives (clock-end_a)/(start_b-end_a) between two keys, or None outside it."""
    if end_a <= clock_hours < start_b:
        return (clock_hours - end_a) / (start_b - end_a)
    return None
'''
open(p,'w',encoding='utf-8').write(s)
p='work/v19-lighting/test_lighting.py';s=open(p,encoding='utf-8').read()
s=s.replace("    def test_region_weight(self)","    def test_key_transition(self):self.assertEqual(M.key_transition(5,4,6),.5);self.assertIsNone(M.key_transition(7,4,6))\n    def test_region_weight(self)")
open(p,'w',encoding='utf-8').write(s)
f='outputs/scene-v19/lighting-provenance.json';P=json.load(open(f))
P['time']=[r for r in P['time'] if not r['claim'].startswith('Exact blend')]+[{"claim":"Transition factor = (clock-end_a)/(start_b-end_a)","status":"native_confirmed","consumer":"FUN_00c7c710"}]
P['constants'].append({"claim":"Fog depth input is clip-space w","status":"shader_confirmed","evidence":"One vertex shader computes mad(cb1[1].x, r0.w, cb1[1].y)"})
P['unresolved']+=["Whether opaque geometry receives fog; fog is not applied in v0.15","Which shader is bloomcapture; embedded shader blobs are not name-mapped"]
P['renderer_v0_15']={"status":"built, packaged, not installed, not visually verified","implemented":["Region ambient cube sampled by N.xzy","(1-sunTerm)*shadow color","sun constants","native point-light form"],"omitted":["specular","SSAO","shadow maps","fog","bloom","color correction","backlight","time-key blending (Noon only, shop fields checked at build)","region blending"],"hypotheses_used":["Cube channel order RGBA","Cube face order maps directly to GL faces"]}
json.dump(P,open(f,'w'),indent=1)
apk=hashlib.sha256(open('outputs/scene-v19/opem-amalur-scene-v0.15-arm64.apk','rb').read()).hexdigest()
t="""Open Amalur V19 shared lighting recovery, 2026-10-31. No game launch and no device action. Tablet remains on v0.14.0.

BINDING: Space root +0x34 is the region asset id (FUN_00fc6800); 943 of 950 spaces resolve. Region root +0xE8 holds cubes, one 0x570 record and day-division hours (FUN_00fcb620, FUN_00ce21d0). FUN_00ccb310 converts the record to the 0x314 runtime entry. Lighting decodes from region and space files alone; no save is required.

SHOP: Region 524912 values and direction equal lighting_int_dal_gorhartinn_region, with no other shipped preset matching. Value equality only; no name is stored. Its cube pixels are the same in DATA and patch.

CONSTANTS (FUN_00cd6680, FUN_00c8a880, FUN_00cd6b70): sun = rgb*hdr*intensity; sun direction = -direction; shadow = rgb plus opacity; fog = (density/500000, fog_start), factor min(1, 2^-(a*w+b)). Point lights (FUN_00ccf660): rgb*hdr*multiplier, saturate((end-d)/(end-start)). Time: hours copied to the time manager, transition (clock-end_a)/(start_b-end_a) (FUN_00c7c710).

VALIDATION: 883 of 884 regions decode; 860 match a shipped preset on all compared fields plus direction, across 94 presets; 23 are listed in decoder-validation.json. All tests in test_lighting.py pass. 440 unique shaders disassembled.

RENDERER: work/v19-host builds v0.15.0, a separate stage. APK outputs/scene-v19/opem-amalur-scene-v0.15-arm64.apk, sha256 %s. Input tests 45 pass; glslc accepts an adapted copy of the shader. NOT installed, NOT seen on a device, so brightness and appearance are unverified. Native parity is NOT claimed. Omitted and hypothesis items are in lighting-provenance.json under renderer_v0_15.

OPEN: See unresolved list in lighting-provenance.json. Next: install v0.15 only with user approval and compare with v0.14; decode luminance_shift.bxml alignment; trace final constant-buffer write.
""" % apk
open('outputs/scene-v19/PROGRESS.txt','w').write(t)
c=json.load(open('outputs/scene-v19/continuation.json'))
c.update(status='binding-solved-renderer-built-not-installed',android_version_installed='0.14.0',android_version_built='0.15.0',apk_built=True,apk_sha256=apk,device_touched=False,game_launched=False,native_lighting_parity_verified=False,blockers=P['unresolved'])
c.pop('android_version_unchanged',None)
json.dump(c,open('outputs/scene-v19/continuation.json','w'),indent=1)
open('work/CURRENT_STATE.txt','a',encoding='utf-8').write('\nV19 UPDATE: space+0x34 region binding and record converter solved; v0.15.0 built in work/v19-host, not installed. Tablet still v0.14.0. See outputs/scene-v19/PROGRESS.txt.\n')
print(apk)
