# Native three-cascade directional shadows

Read-only native export/capture analysis, new research files only. CaptureSHA25672c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209; executable SHA in manifest. No game/renderer/database execution or core edits.

## Ready-to-integrate module

oa_native_shadow.c/.h with oa_native_shadow_math.h implements live-camera three-cascade setup and active native resolve. Caller supplies current GLVP, sunDir, optional actual cameraeye, optional current config. Defaults reproduce native global map bounds and measured reference cascade profile; no saved player locations, recorded VP matrices or per-room branches.

Call open(p,1024), update(p,liveGLVP,liveEye,liveSun,optionalConfig). Then for i=2,1,0: begin(p,i), root_draw_casters(p->cascade[i].vp), resolve(p,i,sceneDepth,ao.fbo[2],width,height).

AO target starts(AO,1,1,1). Resolve samples no colourtarget feedback: ordinary blending reads existingG. Root owns castershader choice, materialalpha/skinning, casterselection/culling exceptions, state restoration and GPUtesting. Sequence follows matching depth-only prepass andAO, beforematerial shading. begin sets conventionalGL CCW/backculling, LEQUAL, depthwrites, no polygonoffset. resolve resetsRGBA mask afterward but leaves depthwrites disabled and postbindings changed.

Supports symmetricperspective GLVP, arbitrary eye/orientation/sun. Skew/ortho/off-centre cameras explicitly return0. config.projection_scale=(pureGLProjection[0],pureGLProjection[5]) preserves original FOVprecision beforeviewrotation; zero derives from liveVP. The latter can shift snap by one1024maptexel at a roundingboundary. Actualeye optional but preferred over recovery from translated floatVP. Inputs are ordinary livecamera data, neverroom/save metadata.

## Active recorded pipeline

Geometrypasses99/101/103 have513/127/89draws, all1024² using ONE reusedD16_UNORM image182/view243, cleareddepth1 eachpass. Immediately resolve100/102/104 samples view184 of thatD16image plus sceneD24depth169. Resolvepipeline7530, VS1899, PS1900; shipped matching966ca4dd9891f20a.asm corroborates fieldnames.

Resolve writes onlyG intoRGBA8image179/view239 (sampled later as181). Otherchannels preserved. BlendSRC_ALPHA + ONE_MINUS_SRC_ALPHA, ADD, no depthtest/writes. Far→middle→near order preservesoverlaps. Shadow sampler1905: linear min/mag, nearestmip, clampedge, compareLEQUAL. ActivePS1900 uses ONE hardwarebilinear depthcomparison, not shipped4/9/16tap alternatives. Scenedepth sampler145 nearest/clamp. Caster rasterbias enable0. Do not add invented outside-frustumwhite behavior.

96-byte constants: texture_size(float4), split_values(float4), screen_to_light(matrix). Shader: Z=1/(invDepthTransform.x*sceneHardwareDepth+invDepthTransform.y); Q=screen_to_light*vec4(screenNDC.xy*Z,Z,1); alpha=min(saturate(Z*split.x+split.z),saturate(Z*split.y+split.w)); result=vec4(compareLinearLEQUAL(shadow,Q.xyz).xxx,alpha). G=result.g*alpha+oldG*(1-alpha), quantizedUNORM8 aftereachpass. Module equivalently uses livecameraZ=B/(depth-A). No2*d-1 inside storeddepth equation. D3DcasterVPZ maps once toGLclip-1..1; receiverQ.z stays0..1. Flip native top-left shadowUVY only at GLdepthsample.

## Source-backed dynamic construction

Anchors:
- FUN_00d13ed0 creates cascades fromprofile, overlaps and globalmapbounds.
- FUN_00d13500 builds frustum-sphere, padsradius, rounds worldcentreXY, sunlookview, extends ortho nearplane to scene-bound minimum.
- FUN_00cf2ea0 makes8frustumcorners; FUN_00d13420 uses BHG::SphereBuilder; FUN_00aee100 enclosing-sphere routine.
- FUN_00ae4140 lookview/worldupfallback; FUN_00abd910 matrixinverse; FUN_00abc7b0 bounds-cornertransform.
- Static overlaps019668a8=(60,100,400,1000,...). Capture3cascade splits1/500/1500/10000. Profiles019668bc..019669ec are runtimeBSS zeros in executable; qualitymenu-index→profile mapping notclaimed.
- Actual receiverQ.zbias table01966258: near−.00008,mid−.00015,far−.0004. Separate table01966244=−.001/−.0015/−.002 appears in matrixc5.w=1+bias, UNUSED byPS. Largerbias is NOT receiverQ.zbias.

Symmetricfrustum: tanX=1/projectionX,tanY=1/projectionY,t2=tanX²+tanY². Rangesnear→far=(1,500),(440,1500),(1400,10000). centreZ=min(far,(1+t2)*(near+far)/2). sphereRadius=sqrt(t2*far²+(far-centreZ)²). halfExtent=sphereRadius*(resolution+4)/resolution. C=eye+cameraForward*centreZ. Round C.x,C.y to nearestinteger tiesawayzero. D=−normalize(sunDir), R=normalize(cross(worldUp,D)), U=cross(D,R). lightPosition=C−D*(halfExtent+.01). nearZ=minimum dot(D,worldBoundsCorner−lightPosition), farZ=2*halfExtent+.01.

Ortho rowsR/halfExtent,U/halfExtent,D/(farZ−nearZ). ClipXYtranslation snaps to nearest2/resolution. Ztranslation=−(dot(D,lightPosition)+nearZ)/(farZ−nearZ). Native globaldefault boundscentre(−25,−25,4921.98388671875), halfextents(125000,125000,50000), from mapbounds expanded to configured fullsize250000x250000x100000 inFUNd13ed0. Exposedconfig handles actual world/configchanges; no room/save matching.

Capturedhalfextents443.05729/1317.77596/8785.17290 matchanalytic geometry<.12ppm. Matrix-only FOV recovery isclose but nearcascade lies by roundingboundary; pureprojectionvalues preserve exactnative snapselection.

Fadevectorsnear→far: (1,−1/60,−1,500/60); (1,−1/100,−440,1500/100); (1,−1/400,−1400,10000/400). Native combine laterusesmin(Lambert,1+shadowColor.a*(G−1)); no hand-tuned strength added.

## Verification and limits

shadow-validation.json compares live-generatedcasterVP against original casterWVP factored by itsworldtransform and originalscreen_to_light bytes. Production module stores no capturedVP. Testinputs are recordedcameraeye/sun and pureprojection scales fromnativeAOprojection fields. Maximumabsolutecastermatrix errorsnear/mid/far1.04e−6/4.20e−7/2.14e−7; resolveerrors1.31e−5/4.80e−6/6.71e−7 (remaining nativefloatoperation-rounding differences). All6clipXYsnaps agreewithin floatprecision. Livecamera motion changesgeneratedmatrices. Bothshaders passGLSL300ES syntax; WindowsCcompile recorded separately. NoGPUrun orvisualparity claim.

This recovers portableCSMsetup/filter/merge. Rootmust drawcorrectstatic/skinned/cutoutcasters andvalidateGL/D3Dcoverage. Alternatequalityprofiles/filtervariants/asymmetriccameras/timevaryingconfig are not generalized from onecapturedprofile.
