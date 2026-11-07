# Reference projection/depth sanity check

No projection change is supported. Actual reference host matrix in `work/v44-native-fidelity/bridge-native-final-r2.json` is bit-exact to captured main-pass CB2@639296 after converting the native D3D depth row to GL: `GLrowZ = 2*nativeRowZ - rowW`. All four converted Z coefficients match after float32 rounding; all XY/W coefficients are unchanged.

Native VS877 stores its computed clip position directly at SPIR-V `%209 -> gl_Position`; no shader Z remap exists. Current world VS in `work/v19-host/oa_post.c:18` also directly stores `mvp*vec4(pos,1)`. Relevant captured viewport event62519 persists through draw68811: x0,y864,width1536,height-864,minDepth0,maxDepth1. Negative height adapts Y; it does not remap depth.

Captured CB2 rows6/7, retained as `native-cb2.bin`, are `(1/524288,0,524288,26.18619155883789)` and `(-0.03818615898489952,0.03818806633353233,0,0)`. They reconstruct `Z=1/(inv.x*depth+inv.y)` from native stored0..1 depth.

Current `work/v19-host/oa_native_dof.c:14` helper, evaluated from the exact float32 host VP, derives A=1.0000499622778718,B=-26.187554366567284 and inverseDepth=(-0.038186077028512955,0.03818798437714577). Differences from native inverseDepth are +8.1956386566e-8/-8.1956386566e-8, resulting from float32 composed camera matrix cancellation. At physicalZ11000, it reconstructs11000.0626; CoC=.051285 instead of.051282, approximately13/255. AtZ10912.625, CoC=.046916, approximately12/255. This cannot explain effectalpha91/255.

A uniform CoC91/255 would implyZ17111.9233 with start9974.311523/range20001. But effectalpha is sampled from LINEAR half-resolution fuzz, not computed from the exact full-resolution leaf fragment. At native full pixel(800,150), the four contributing halftexels are(399,74),(400,74),(399,75),(400,75), weights1/16,3/16,3/16,9/16. Those halftexels nearestfetch native full-depth pixels(799,149),(801,149),(799,151),(801,151). Different depth coverage there could raise alpha legitimately; raw attachments are needed to attribute it.

Source precision issue, separate from projection: current fuzz shader declares `uniform sampler2D depthTex` with no sampler precision qualifier. A read-only glslang comparison of its source (version bumped300→310 solely for SPIR-V export) decorates the sampler, OpImageFetch and fetched component with RelaxedPrecision. Changing only to `uniform highp sampler2D depthTex` removes those decorations. Native1841 SPIR-V has no RelaxedPrecision decorations. Therefore explicit highp is supported by the native precision contract. This compiler probe does not establish what the deployed GPU compiler actually chose, nor prove it caused observed91alpha.

`projection-numerics.json` preserves exact coefficients and numerical examples. Source snapshots are read-only copies, not implementation edits. No replay, GPU test, Ghidra call or asset/source deployment was performed.
