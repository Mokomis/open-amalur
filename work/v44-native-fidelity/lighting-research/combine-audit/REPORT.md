# Current native lighting arithmetic audit

2026-11-05 read-only audit. Snapshot is current authoritative work/v19-host/oa_post.c copied at audit start, SHA256acf3b3db58f10a2ebe95eea9a055f76d7d748c1d3f7c8c265f0e677fc408c55c. Source and two requested screenshots were read; no shared files edited, renderer/UI/game launched, database mutated or tool installed. Root owns applying fixes and GPU/tablet comparison.

## Minimal supported fixes

1. Native point lights must accumulate diffuseRGB plus scalar luminance-weighted specular into RGBA16F, then reconstruct coloured specular in the deferred combine. Current light() adds independent coloured specular per light and omits the N·L factor in those highlights. Exact replacement snippets are native_point_replacement.glsl, including variable declarations, light(), reset and final consumption. The feature128OFF legacy branch is unchanged.
2. Saturate lighting BEFORE fog, preserving the native UNORM8 intermediate. Current mix(lit,fog,F) allows HDR lighting to survive through fog and only clamps on the final store. This can produce too-bright/yellow highlights without any wrong sun or point-light intensity. The native boundary is a real RGBA8 store; a collapsed shader can use clamp plus nominal8bit rounding. Rounding ties depend on the GPU conversion; exact storage requires a real intermediate target. Saturation itself is unambiguous.
3. Evaluate fog per pixel from physical forward depth, not an interpolated exponential evaluated at vertices. Current normalized perspective GLVP has forwardZ=1/gl_FragCoord.w. Keep the recovered density/start. Also retain the native direction-dependent sun fog tint(.5,power10); do not retune fog colour.

native_fog_replacement.glsl gives the native128-only replacement and exact constants. proposed-world-fragment.frag combines both snippets into a NEW diagnostic copy of the audited current shader, not the shared file. All7variants compile as GLSL300ES. Root may already have applied newer source changes after this snapshot; do not overwrite them with the diagnostic copy.

## Sunlight, shadow and AO equation is already correct for this reference

Independent direct interpretation of active fragment1895 versus the current mathematical equation passes250randomG-buffer/local-light/AO/shadow cases with maxRGB7.15e-7. No sunRGB, shadowRGB, ambient scale or backlight adjustment is justified by this audit.

Let N=normalize(half(Nmaterial*.5+.5)*2-1), I=camera-to-fragment unit direction, d=N·sunDir, A=AO, H=shadow. Native front=min(saturate(d),1+shadowColor.a*(H-1)). Captured shadowColor.a=1, so current min(saturate(d),H) is exact here. Backscale=A*.1199999973 and directDiffuse=front+saturate(-d)*backscale.

Ambient term is A*(G2ambient+(1-front)*shadowRGB*G1albedo). Direct diffuse is(sunRGB*directDiffuse+localRGB)*G1albedo. AO does not multiply direct sun or local diffuse/specular. Current source has that placement correctly.

Sun reflected lobes are pow(max(saturate(±dot(sunDir,reflect(I,N))),1e-5),halfGloss*.25). Front lobe is zero when d<0. Sun specular factor is frontLobe*directDiffuse+backLobe*backscale, multiplied by sunRGB and stored half G1spec once. Current source implements this correctly. All active phase97 shiftIds are below.5, so absence of wrapped-diffuse selection does not change this reference. A future wrapped material needs the separate recovered flag contract.

Native pointPS1870/1871 ALSO decode and renormalize G0normal before using it. Earlier consideration of raw decoded point normals was rejected by the actual shipped and active instruction streams. Current N is the right point-light input. Gloss is G0.a*.25, with no extra fixed exponent20/32 in the native point contract.

## Point aggregation and constants

For each accepted light, with unit Ld toward light and atten=saturate(dist*mul+add):

```
nl=saturate(dot(N,Ld));
lobe=exp2(log2(max(saturate(dot(Ld,reflect(-V,N))),1e-5))*storedGloss*.25);
RGB=(nl*lightColor)*atten;
alpha=dot(((nl*lobe)*lightColor)*atten,(.2126,.7152,.0722));
```

The material specular strength is NOT used in this per-light pass. The target starts0 (clear record72653), RGBA16_SFLOAT image164/view237. Colour and alpha blendONE+ONE. Pipeline7534's21draws have colourWriteMask0 and only establish stencil;7536's21plus7539's40 are61actual light contributions. Do not count the82recorded draw calls as82lights.

Each accepted target blend stores HALF(previousStoredHalf+newFloatContribution). This means half rounding after EACH contribution, not rounding each contribution first and not only the final total. The snippet preserves this boundary. The current8-entry spatial grid and light ordering remain separate limits: exact native per-pixel draw order can change small half-rounding results, and omitted overlapping lights would be another issue. This audit did not infer extra lights or change their authored data.

Combine1895 reconstructs:

`localSpecRGB=localRGB*localAlpha/(dot(localRGB,(.2126,.7152,.0722))+1.0000000116860974e-7)`.

Final material spec term is `(sunRGB*sunSpec+localSpecRGB)*G1spec`. Current per-light vector highlights both omit Lambert and bypass this luminance/colour reconstruction. This is the principal point arithmetic fix. Unknown materialFamily0 is a legacy fallback: its old spec_sum*.9 is not a verified native material contract. The snippet calls that out rather than inventing one.

All61unique active light constant pairs were matched to the current1088authored town_live entries. Largest position difference .0304world units is from C text precision. Native/source RGB ratios differ from1 by at most4.5e-7; attenuation slope error≤4.54e-10 and add error≤3.96e-7. The original fields are mul=−1/(outer−inner),add=outer/(outer−inner), exactly the same linear sphere law as current inner/outer falloff. There is no evidence for changing colour channels, intensity, decay law or radius here. point-light-source-comparison.json preserves every match.

Direct CPU interpretation of active pointPS1870 versus the proposed contribution arithmetic passes200cases, maxRGBA2.16e-7. Shipped equivalents628b10586ca02f57/ca8e4d95a707f0b8 are retained; their final kernels agree and only their position reconstruction differs.

## Quantization and fog order

Material boundaries currently emulated correctly: G0normal encoded without invented clamp then half; G0gloss half; G1albedo/spec saturated then half; G2ambient saturated then half. Ambient Q uses raw material specular before G1saturation. Material sky/cube ambient is computed before deferred N is re-normalized, as the native material producers do. The captured ambient cube R/B correction is independently proven; grass image7499 has the same tight pixels as main7496, so there is no separate grass cube variant to tune.

The missing boundary is scene lighting output. Active phase106 PS1895 writes RGBA8_UNORM image173. Phase107 sky fills background. Phase108 first draw72947 (PS134) copies image173 into RGBA8image176 and subsequent transparent draws composite there. Phase110 PS1898 reads that8bit image176, evaluates screen fog and writes8bit image173 again. Current forward shader collapses those boundaries and fogs unclamped HDR values.

For example rawlit(1.5,1.2,.7),fog(.42,.36,.22),F.2 gives current stored colour approximately(1,1,.604), while the pre-fog saturated native result is(.884,.872,.604), before considering its small8bit rounding differences. This demonstrates the yellow/highlight mechanism, not a measurement of those exact HDR values at a screenshot pixel.

Native fog depth is reconstructed from hardware depth into physical forwardZ; ray length is not used for extinction. Its transmittance is min(exp2(−1.44269502*(density*Z+start)),1). The current exp expression is mathematically equivalent but should be evaluated at the fragment, not at vertices and then interpolated. Using reciprocal gl_FragCoord.w is valid for current normalized perspective GLVP. If a future projection carries a homogeneous scale, recover the corresponding scale instead of assuming it.

Fog ray is normalized ONLY for directional tint: tint=.5*max(dot(normalize(W-eye),sunDir),0)^10; fogRGB=mix(fogRGB,sunRGB,tint). This is separate from the forward-distance extinction. On the central bridge ray dot≈.127, so this tint is negligible there; do not blame that direction term for central path brightness.

Independent interpretation of active fog1898 versus this equation with a zero distortion field passes200cases, maxRGB1.19e-7. Screen distortion/transparent layering are separate native inputs, not covered by this collapsed opaque-world replacement. Native sky and independent native water have separate producers/order and should not be moved into this opaque pre-fog quantization branch.

## Actual reference globals

sunRGB(.7858883142,.7858883142,.7858883142); sunDir(0,.3654382229,.9308354855). shadowRGBA(.2000000179,.1450980455,.1098039299,1). skyLight(.5,.5,.6000000238,1),ambientDiffuseScale5,ambientSpecularScale.8999999762,backlight.1199999973. FogRGB(.4196078777,.3607843220,.2235294282),density4.7310200898e-5,start−.1552170217,sunlightFogTintAmount.5,power10. Raw1376byte globals and native-constants.json preserve the values. Current authored/uploaded sun/fog values agree to text/float precision. No brightness tuning is proposed.

## Limits

The inspected screenshots show bright/yellow bridge/path and dark leaf cards, but static arithmetic does not uniquely attribute every visible difference. The supported fixes above are real contract differences regardless of screenshot interpretation. Leaf material/geometry/texture coverage, shadow caster coverage, light-grid budget, actual GPU UNORM rounding and scene sampling need root's runtime evidence. The core sunlight/AO equation is validated; changing it to compensate for remaining visual differences would discard confirmed native behavior.
