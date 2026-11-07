# v35 verified update — 2026-11-05

VersionCode9 / versionName0.9-native-geometry is installed. Native geometry branch ACTIVE on tablet. native-geometry-v9-zero-30 logs30replacements,0rejections and first/last/raw Android replay RGB bit-identical at1536x864. native-geometry-v9-pose-30 at user's saved yaw0.14175,pitch0.089045 also logs30replacements,0rejections and identicalfirst/last. No performance numbers claimed for these screenshot checks. Viewer restored visibly to user's pose, live run log files/native-geometry-live/replay.log. Screenshot evidence/tablet-native-restored.png. No further UI input needed.

APK SHA256c169b22757e0f977e6df5f7628019289b805001945850743b7dcf77d0e85f7a8; native library2ac1acd3ec9a8fdd13b0fdd5c5a4ad0a979c8240cdf500874ba27f751749a4f0. All older sources/APKs retained, original app/key/save untouched. Native packet1938indexed draw maps by exact resource content tolive Vulkan drawblock69921. This replaces ONE geometry tail perframe; material/pipeline/shaders and all other draws are still captured. Fullengine is not ported.

Further work now in v36-native-ranges: kind1 geometry decoder validated against474indexed real native draw; hostASan/UBSan anddirectAndroidARM64probe both exact,4negativechecks. The596byte fixture deduplicates identicalformat/stridealiases. Runtime scopeexplicitcount474andzerooffsets; fallback/nonzerooffset branches need additional native coverage before broadclaims. Constant metadata6records*48bytes; per-instance constant-copy capture is pending in v34 tools. No v36 integrationAPK build yet.

--- Earlier implementation checkpoint follows ---

# v35 native geometry integration IN PROGRESS — 2026-11-05

Read canonical AGENTS then ../open-amalur-native-camera/CURRENT_STATE.md and ../open-amalur-native-packets/CURRENT_STATE.md.
Authoritative Windows work/v35-native-geometry, copied v33 source into separate source/build; v33 and current tablet v8 preserved. Sol High, no agents/Astra. Source patch ready,221-step build PASSED, packagingv9 now(session from latest tool).

New OaNativeGeometryBridge class in framework/decode. Portable sparse Cdecoder/backend compiled into native Android library. Fixed548byte real kind0 packet from v34 resource capture embedded privately. Exact resource-content bridge maps VBtokens to captured Vulkan buffers3704/1831,IB3706. Target captured drawblock69921,cmd46,pipeline13175,indexCount1938,firstIndex/vertexOffset/firstInstance0,instances1,VKUINT16,strides28/28,offsets0.

Root consumer tracks actual VB2/IB/pipeline bindings and begins percmd state. On targetdraw, decode original sparse guest32bit object snapshot, run recovered geometry backend callbacks (VB/topology/IB/draw), verify tokens/counts/resources/strides/pipeline, then produce actual base Vulkan CmdDrawIndexed arguments from that submission. All other state/material/shader setup stays captured. Explicit guards reject and fall back to original args. Logs prove enabled/decoded,first submission,destructor replacements/rejections.

Feature OA_ENGINE_GEOMETRY env is process-only, set by intentextra oa_native_geometry=1; default launcher enables it; explicit host args withoutflag keep it off. Host oa-launch-native-geometry.py adds --engine-geometry to v33 runner. Other camera controls preserved.

Latest packageversionCode9/versionName0.9-native-geometry, packageorg.openamalur.nativebenchmark,same own debugkey in v32. APKfolderapk-native-geometry. NOT INSTALLED/NOT RUNTIMEVALIDATED yet. Next: getAPK, preserve currenttabletpose from camera-default.log(lastobservedhuman pose yaw0.14175 pitch0.089045), install ONLY benchmark app, zero30screenshots engineON confirm30replacements,0rejections andRGBexactmatchraw. Then moved-camera test runtime. Save results/sourcehashes on both hosts. Restore user's pose. Screen look beforeinput. No original app uninstall/key changes. Tabletowner seems to have testedtouch, do not resetviewneedlessly.

v34 has additional successful kind1 capture while v35built: capture2026-11-05T20-38-32-454Z. Firstkind1nativepacket0x2d791308,geo0x05093160,range0x05074480,holderstrides&format both0x09da5254. NativeVB tokens0xaaad9890/0xaa902fb0,strides60/8,offsets0,IB0xaaad9728,format57,topology4,DrawIndexed474. All detached269ms,gamepaused. CPU8namedspans include duplicate aliasesformat/strides atsameaddress—dedup exactbyte-identical spans before sparse reader, which rejects overlap. Not ported/validated kind1 decoder yet. Could next recover range/offset/fallback fields from source draw_kind1 plus original assembly, verifythisactualcase; no fixedstride shortcuts.

v34 correctness: firstfunction-ENTRY snapshot mismatched stride12vs0 because shader/materialsetup changes holder+0x2c. Corrected capture boundary to immediatelybeforeIASetVertexBuffers, no decoder stridebug and NO constant12fix. Correct packet1812 and secondpacket1938 both passhostASan/UBSan anddirectARM64 geometryproof,4negativechecks. v31oldsource untouched. v33native matrixkernelmatchesoriginalx86/ARM64on4221casesandall1598actualcapturedprojections. v33APK8currentlyvisibleandinteractive. All19PCsaveshash-matchbackup afterruntimehooks. No gameplayinputwasneededonWindows.
