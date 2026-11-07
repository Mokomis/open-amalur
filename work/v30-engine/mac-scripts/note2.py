import json,hashlib
apk=hashlib.sha256(open('outputs/scene-v19/opem-amalur-scene-v0.16-arm64.apk','rb').read()).hexdigest()
c=json.load(open('outputs/scene-v19/continuation.json'))
c.update(status='installed-v0.16-rendering',android_version_installed='0.16.0',android_version_built='0.16.0',apk_sha256=apk,previous_apks=['outputs/scene-v18/opem-amalur-scene-v0.14-arm64.apk','outputs/scene-v19/opem-amalur-scene-v0.15-arm64.apk'])
json.dump(c,open('outputs/scene-v19/continuation.json','w'),indent=1)
f='outputs/scene-v19/lighting-provenance.json';P=json.load(open(f))
P['renderer_v0_16']=dict(P.pop('renderer_v0_15'),status='installed on tablet; rendering; native parity not claimed')
R=P['renderer_v0_16'];R['implemented'].append('Color LUT 1525613 sampled at color*0.9375+0.03125')
R['omitted']=[x for x in R['omitted'] if x!='color correction']+['color-correction brightness and color_transition terms']
R['hypotheses_used']=[x for x in R['hypotheses_used'] if 'channel' not in x.lower()]+['Cube channel order RGBA','LUT half-texel mapping for a 16-entry LUT; native rawUVadjust values not traced','LUT applied to clamped lit color with no bloom']
P['color_correction']=[{"claim":"Asset 1525613 is a 16x16x16 RGBA8 LUT with a 38-byte header, indexed (r,g,b)","status":"asset_verified","evidence":"Size is exact; black, white and primaries land on their corners with RGBA order"},{"claim":"Merge pass constants source","status":"hypothesis","evidence":"Packet 0x42 copies 0x48 bytes; the draw writing the 0x40-byte merge buffer was not found"}]
json.dump(P,open(f,'w'),indent=1)
p=open('outputs/scene-v19/PROGRESS.txt').read()
p+="\nV0.16 INSTALLED: adds color LUT 1525613 to the room shader. Tablet 99cc517a runs 0.16.0, APK sha256 %s. Screenshots tablet-room-lighting-v0.15.png and -v0.16.png share the fresh-launch camera. Rollback APKs are kept. Native parity is NOT claimed.\n"%apk
open('outputs/scene-v19/PROGRESS.txt','w').write(p)
open('work/CURRENT_STATE.txt','a',encoding='utf-8').write('\nV19 INSTALL UPDATE: tablet now runs v0.16.0 (adds color LUT). See outputs/scene-v19/PROGRESS.txt.\n')
print(apk)
