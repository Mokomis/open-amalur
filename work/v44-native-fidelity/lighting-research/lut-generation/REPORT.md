# Active LUT generation identity and final effect layer

Static capture/source audit, 2026-11-05. New files only. No GPU, game/UI, installation or database mutation. Recording SHA25672c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209.

## Identity proof: no LUT retune

Current work/v19-host/room_lighting.c uploads opem_town_lut as GL_SRGB8_ALPHA8 16³. All16,384 source bytes from current town_environment.inc exactly equal ACTIVE LUT source image4443/view4447, VK_R8G8B8A8_SRGB. SHA256a0a3af8c0315a4f1394218c71c5c113bda4a8a99546804d615e6760245453494. This is a byte comparison against the recording's original InitImage payload, not a filename inference. The other bound source image1833 differs, but its weights are zero.

Active phase134 draw73395 VS1854/PS1855 writes UNORM RGBA8 image1862,256x16. Input images0/1 both4443; images2/3 both1833. Sampler145 NEAREST, clamp all axes. Uniform64bytes at memory52+1765632:

```
c0=(0,0,0,0)
c1=(1/16,1/32,0,0)
c2=(0,0,0,1)
c3=(1,0,1,0)
```

The full-screen triangle has UV [(0,0),(0,2),(32,0)] over clip [(-1,1),(-1,-3),(3,1)]. Its 256x16 raster centres map to source3D coordinates ((r+.5)/16,(g+.5)/16,(b+.5)/16), where atlasX=b*16+r. PS1855 performs:

1. q=(fract(uv.x),fract(uv.y),floor(uv.x)*c1.x+c1.y).
2. C01=mix(texture0(q).rgb,texture1(q).rgb,c0.x).
3. C23=mix(texture2(q).rgb,texture3(q).rgb,c0.x).
4. C=mix(C01,C23,c0.y).
5. C=exp2(log2(C)*c3.x).
6. L=dot(C,(.2126,.7152,.0722)).
7. C=C*c2.a+c2.rgb*(L*c3.y+c3.z).
8. Output=(C,dot(C,(.2126,.7152,.0722))).

Thus ACTIVE generation is exclusively the sRGB-decoded image4443, with neutral exponent/gain/tint. It does NOT contain another saturation, exposure, contrast or palette correction. Current source selection and sRGB decode are correct.

## Only remaining LUT difference: UNORM quantization boundary

Native generation writes decoded values into8bit UNORM before final interpolation. Current sampler3D path interpolates the decoded source values without that intermediate8bit rounding. With this actual LUT, nominal sRGB decode then UNORM rounding has maximum RGB difference .00180586033 (0.4605/255), mean .000813326. Convex trilinear interpolation cannot amplify that lattice bound. Native driver's sRGB conversion/UNORM rounding can differ slightly from the nominal formula; no native GPU atlas readback is available to claim byte-exact generated output.

Optional nominal quantized16³ RGBA and256x16 atlas files are supplied. The atlas OATX is GL_RGBA8, one level. These are generated reference data, not a justification to visually retune the LUT. Switching the current3D upload to these linear bytes would preserve the native quantization boundary while retaining current3D sampling coordinates. Raw alpha is generated luminance; final grading only consumes RGB. Native final merge later recomputes final alpha using(.299,.587,.114) for AA.

## Final merge effect-layer influence

Active PS1858 combines BEFORE grading:

`C=clamp(scene.rgb*(1-effect.a)+effect.rgb*effect.a+bloom.rgb*.4306860566,0,1)`.

An effect texel with alpha0 is exactly neutral, even if its RGB is stale. However image176/view178 at this stage is NOT an empty particle layer. Its last producer is phase117 PS1849, the native depth-of-field resolve. Sources are the scene image173 and half-size fuzziness image197. Shipped equivalent1254fa3a99311a33.asm names sceneTextureSampler/fuzzinessTextureSampler and tapScale; its16 offsets match active1849.

Near-CoC PS1839 is identically zero here because active near parameters c0.xy=(0,0); its quarter downsample/blur remains zero. Far-CoC PS1841 reconstructs normalized depth Z/524288 and computes:

`farCoC=min(max((Z/524288-.0190244894475)*26.2130889893,0),.6999999881)`.

It starts at9974.3115world units and caps at23975.0115. The fuzziness texture's R is blurredNearCoC+gatedFarCoC, G normalized depth, and B marks the far region. PS1849 writes centre fuzzinessR as effect alpha and a16tap depth-aware weighted scene blur as RGB. Its tapScale=(6/1536,6/864) at this reference extent. Foreground below~10k therefore has alpha0 and no final DOF influence; distant canopy/background can blend up to70% blurred colour. This can affect distant contrast/detail but is not a global colour transform. Root owns any future portable DOF integration and visual test.

The LUT identity question is answered: do not attribute a large red/green or overall contrast difference to a wrong authored LUT. No shared source/assets were changed.
