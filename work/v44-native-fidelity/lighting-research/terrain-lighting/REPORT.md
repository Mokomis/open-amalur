# Native terrain material and vertex basis

Read-only original capture and exported native code analysis, 2026-11-05. New research files only. Capture SHA256: 72c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209. No game, live renderer, UI, database mutation, installation or helper inference. Root owns shared implementation and runtime integration.

## Concrete integration

`native_terrain_vertex.glsl` supplies the source-derived tangent basis, per-vertex worldVector transformation and native terrain position/UV mapping. `native_terrain_fragment.glsl` supplies exact blend weights, material normal/albedo/specular packing and ambient calculation. `native-792.frag` is an independent mechanical translation of the ACTIVE captured PS with every SPIR-V ID retained; it compiles as GLSL300ES. The concise helpers also compile. Raw active shaders, shipped shaders, original vertex buffers, constant contracts and source producer bodies are retained.

Independent CPU evaluation of active PS792 against the concise material/ambient formulas passes 300 randomized texture/material/paint/basis cases: maximum G0/G1/G2 difference 1.383e-5, cube direction 3.142e-6 (float32 versus high-precision reference). This checks shader arithmetic, not GPU execution or final F16 quantization. Root still owns runtime image checks.

## Active shaders and material fields

Phase97 uses pipeline7526 with VS791/PS792 for 94 terrain draws. The shipped VS8bf24b8dc30a668c and PS1bc6cb4d0dcff9cf have the same terrain contract. The captured uniforms bind cb0 material32bytes (levels then powers), cb1 globals1376bytes, cb3 terrain64bytes, cb4 dynamic256bytes. All 94 sampled worldVector matrices are identity, but the native vertex shader explicitly transforms all three basis vectors using the matrix.

Only four distinct material vec4-levels/vec4-powers sets occur in this frame; `captured-terrain-materials.json` and raw32byte files preserve them. This does not remove a fifth authored palette set outside the selected draws. Examples of first layers are level1.385754943/power16.141130447, .969024003/10.681962013, .899389982/47.108680725, 1.034998059/48.732170105. The last three layers are shared here: levels1.0237,2.138845921,1.575752020 and powers2.115314007,43.154724121,49.774394989.

The shader writes weighted powers directly to G0.a. Deferred combine subsequently multiplies G0.a by .25. Do not silently replace the stored authored power by a fixed exponent.

## Authored basis, not derivatives

Vertex layout is exactly48bytes: float3P at0, N at12, T at24, B at36. Runtime vertex stride is48, independently confirmed by vkCmdBindVertexBuffers2. Each vector is worldVector-transformed then normalized separately in the VERTEX shader. The pixel shader receives their perspective interpolations and computes:

`Nworld=normalize(nt.x*T_interpolated + nt.y*B_interpolated + nt.z*N_interpolated)`.

The interpolated basis vectors are not independently renormalized or Gram-Schmidt-adjusted before that mix. The decoded tangent normal nt is not separately normalized first. Replacing these varyings with a fragment derivative basis changes the contract.

The native producer is FUN_00ceb3e0, which calls FUN_00c9dc90 for main terrain vertices and skirts. It computes central-difference height slopes sx,sy and N=normalize(sx,sy,1). It RETAINS the original, unnormalized sx across that normalization. The tangent seed is (1,0,sx), projected off N then normalized; B=cross(N,T). This is an unusual positive-slope seed and must not be replaced by the ordinary downhill tangent.

For an export retaining only source vertex N, recover sx=N.x/N.z, then:

```
seed = vec3(1,0,N.x/N.z);
T = normalize(seed - N*dot(seed,N));
B = cross(N,T);
```

Reconstruct this at VERTICES, then do the native worldVector transform/normalization, then interpolate. All44 unique captured vertex buffers (18,700 vertices) agree with this float32 formula to maximum component error6.55651e-7. Source height slopes or original T/B retain the original rounding most closely. Near the degenerate seed, N-only reconstruction may be ill-conditioned; native source has no guessed fallback branch. The related algebraic cross-seed formula previously messaged is less numerically close and is not the delivered implementation.

The decompiler omits argument effects across FUN_00add3f0; therefore the native x86 assembly was also inspected. At00c9de67 it loads original sx from stack+44 while normalized N.x/N.y/N.z are stack+1c/+20/+24. It builds dot(seed,N), projects, calls normalization at00c9df25 and writes cross(N,T). This is why treating the retained slope as normalized N.x gives a wrong basis for steep slopes. Assembly and raw code bytes are preserved.

## Position and UV coordinates

Native q=sourceP*terrainVertexOffset.w+terrainVertexOffset.xyz. In this frame q is camera-relative: native worldViewProjection has rotation/projection and zero camera translation. VS stores q.xyz in TEXCOORD2 for ambient view direction. Native terrain UV = q.xy*terrainTexcoordMad.xy+terrainTexcoordMad.zw; blendUV=terrainUV*terrainBlendTexcoordTransform.xy+terrainBlendTexcoordTransform.zw. The four layer UV scales are textureTilesPerVertex.x/y/z/w.

For the custom renderer's absolute world vertices, use current FULL GLVP and separately pass q=worldP-eye to ambient. For native camera-relative q, use projection*viewRotation. Do not subtract the eye twice. The helper parameter explicitly states this distinction.

## Blend, specular and paint alpha

Sample paint=(r,g,b,a). The pre-height weights are:

```
w0=r;
w1=g*(1-r);
w2=b*(1-g*(1-r))*(1-r);
w3=1-saturate(w0+w1+w2);
```

This is not interchangeable with ordinary four-layer successive alpha compositing. Multiply by each diffuse alpha, subtract max(weight*diffuseAlpha)-global.terrainHeightBlendFactor, clamp to zero, then normalize their sum. Native sums exactly zero without a special guard only for invalid inputs; authored inputs are the contract.

Blend ALL FOUR channels of normal textures with these normalized weights. Decode RGB*2-1 and transform using the interpolated T/B/N above. Normal alpha is specular strength, not a discarded channel.

Let S=dot(levels,weights)/sumWeights * blendedNormal.a. Let D=weightedDiffuseRGB/sumWeights * paint.a.

- G0.rgb=N*.5+.5; G0.a=dot(powers,weights)/sumWeights.
- G1.rgb=saturate(D); G1.a=saturate(S*paint.a).
- Q=S*global.ambientSpecularScale, captured .9. **Q does not include paint.a.**

Ambient diffuse uses D BEFORE its G1 saturation/half-float quantization. The shader samples the ambient cube at N.xzy (Z-up world to cube component order). Its attenuation is1-saturate(Q).

For I=normalize(cameraRelativePosition), camera-to-fragment, the native sky lobe is saturate(reflect(I,N).z) raised to skyLight.a*ambientDiffuseScale (captured5). Sky RGB is multiplied by Q WITHOUT clamping Q first. Therefore:

`ambient=saturate(cube(N.xzy)*(1-saturate(Q))*D + skyRGB*skyLobe*Q)`.

The source implements the view/reflection sign through E=normalize(-q), negating reflect(E,N).z; the helper uses the equivalent camera-to-fragment I to avoid an extra sign reversal. G2.a is saturate(dynamicLuminanceShiftId), not paint alpha. AO is applied later in deferred combine.

## Evidence and limits

`terrain-draw-contracts.json` preserves every active terrain descriptor/constant and vertex-buffer binding. Each original buffer is retained tightly bounded to its actual VkBuffer size, excluding capture allocation padding. `terrain-basis-validation.json` identifies original memory/fill/file offsets and hashes. `validate_basis.py` only reads the recording and writes research outputs. `validate_fragment.py` independently evaluates the active SPIR-V arithmetic; it does not run GLSL or call the concise helpers. Shader sampling is exercised using random constant textures; texture derivatives/filtering and final visual rendering remain root's integration test.
