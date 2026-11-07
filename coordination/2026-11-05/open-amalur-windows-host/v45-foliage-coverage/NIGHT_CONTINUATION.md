# Current verified state: Open Amalur v0.36 R3 (2026-11-06)

The custom GLES3 replacement engine is the active Android approach. The separate real-engine/FEX work is preserved and paused. Windows and ARM64 builds pass. Native Android v0.36 R3 is installed on tablet99cc517a (package0.36.0/code38), with APK SHA2564a38d2a722519258be04d1a377b3adae24d1efe35bd56d87df4be1ac5582b7e9. The existing signing key was reused on Windows and never copied or replaced; the app was updated in place.

The current update restores source Region trees and bridge-side lamp/cart actors, the correct mossy root and near-detail foreground rock, native foliage attributes, DOF sampling and soft godrays. A separate authored tree-shadow proxy now replaces the proven false leaf-card shadows. Windows live A/B matches native sunlight at both sampled foreground rock pixels. The first supported proxy cohort is34unit-scale FAB343974 placements;22nonunit placements and other families retain the old fallback. Read work/v45-foliage-coverage/FINAL_VISUAL_REVIEW.md for the top/middle/bottom original-image comparison and qualifications.

Actual tablet logs confirm301material rows/42native profiles,175leaf cells,200shadow cells,26Region replacement IDs,17readiness dependencies, proxy GPU draws and shaped soft particles. A short joystick walk advanced6metres; HOME/resume recreated the GLES surface and rendered successfully. Short stationary samples were32.0FPS at2520x1680/thermal1 and47.3FPS at50%linear resolution1260x840/thermal2. They are not a strict baseline or sustained benchmark. A startup profiler GL0x502 message remains documented.

The original save and settings hashes remain unchanged. Temporary position, heading, resolution, profiling and USB stay-awake settings were restored. The app is stopped and tablet asleep. The Windows preview is closed, reference properties restored and OA_CustomEngine_Windows_v40 task returned to its normal --scene town action. The temporary localhost-only ADB/SSH tunnel is closed. Other tools, credentials, databases and helper/model services were not reconfigured.

The remaining clear visual blocker is excess distant canopy at native pixel980,100. Current source198 from South SPACE431642 occupies a native clear-depth pixel. Simple source/alias/bounds-centre cutoff rules reject2of33valid native leaf draws and were withheld. A focused eight-function native pass recovered a separate runtime actor-state propagation path, not the static collection admission/SPACE/LOD selector. The GPU capture lacks the corresponding CPU flags and handles for these fixtures. Continue from exact static registration00fec370 ->00cd24e0/00cd2570, correlating source198 and positive68811; trace the actual static admission consumer or capture its CPU state. Avoid another actor virtual walk, fitted cutoff or reference-frame visibility whitelist. See native-space-visibility/focused-render-selection/REPORT.md.

Other limits remain explicit:73unwitnessed scaled leaf transforms are unchanged, shadow-proxy support is incremental, and godray animation input/sign selection is a qualified candidate. The waterfalls retain the owner-preferred custom style. Their shader branch, four material rows,13texture payloads and water parameters remain identical to R4. No full-scene pixel or whole-game parity is claimed.

Private recovery kit: outputs/scene-v45-r3/restore-delta-v036-r3.zip (58,050,346bytes), SHA256a4407647dc83c54b9dcb496b73afab07a1cc5af4de8ea8fa502bf48f4bf2ea19, verified on the Mac. It requires the preserved R4 baseline and dependencies. It contains actual source, changed assets and ARM library, without the signing key or analysis database. source-build-receipt.json pins the delivered code. The authoritative Windows folder is not a Git checkout; keep clones separate.

For future builds, read OPERATOR_BUILD_GUIDE.md and use build_renderer_batch.py once after a batch of source edits. Existing one-time integration scripts preserve their original input guards and are not the normal build entry point. The previous notes remain below; they are historical where this checkpoint differs. A notes-encoding failure was fully recovered byte-for-byte, with the original file and recovery receipt retained. Use explicit UTF-8 and atomic note writes.

---

# ACTIVE: Windows shadow proxy A/B verified; Android R2 installed, R3 next

ActualWindows A/B: bridge-shadow-proxy-0.png rockAOgreen0; mode1green255 at50,735and100,725, matchingnativeD16reconstruction. Registry200cells/26RegionsourceIDs/17deps, actualGLproxy draws2. Win/ARM PASS, final-renderer-build.json current. 218hashguardedasset overlayspromoted: UNIT34FAB343974shadowproxy9/MID1744210,22nonunitswithheld; exactotherFB/nonunitfallback, sourcealpha7032048sq9mips, fullfloatfamily10wind,301MATS/nativeprofiles,leaf/regionheaders301,indextextures704. Visiblec/l/rgeometryunchanged(rmetadataflags only). Caster-only API explicitly distinguishesnativeCSMfromMAINearlyZ. IndependentproxyownGPUreadiness; fallbackswapwaitsdeps; RegionusesmatchingownReady. Staticreviewpassedafterfix. InspectMac /private/tmp/oa-v45-proxy0/1.png thenpackageAndroidR3.

AndroidCURRENTv0.36.0/code38/R2 SHAe1cd07d48c0e59c68a398aa02d621fcbf2a873cb7ba31b3c7e2cba8d423be838 installedsamekeysuccess; proxiesNOTon tabletyet. R1compressedresourcesrejected-124(noappchange), R2STOREDfixinstalled. Originalsave/settingsmatchedafterinstall. R2runs nativeleaf175/region/native41/FX12shaped; bridge100.png actualnearbridgeATsnapsfeet8714,-87104,6445 onstairs, camera/aspectDIFFER fromWindowsref. EarlygesturewhileblackscreenINVALID; no movementclaimyet.

RESTORE REQUIRED: tabletstay_on_while_plugged_inTEMP2(USB), ORIGINAL0, Macandroid-validation/temporary-keepawake.json. debugprofile1,AT8591.932617 -87036.03125 6493.066406,scale100; baselinebefore/properties.txt; original2files272Btarbefore/app-files.tar. Verify/restoreend. PID5542R2,keyguarddismissed,awake-pre-walk.png ready. Use rootnotrun-as. Needrealwalk/resume/R3feature/100-50sample.

Macdiskapprox1GBfree,twoR1/R2APKcopies; DON'TdownloadthirdfullAPK. WindowsADB tools/android/sdk/platform-tools/adb.exe. localhost15037free; intendedlocalhost-onlySSHreverseADBforwardtoMac5037 letsWindowsinstallWindowsR3directtoUSBtablet; NOTSTARTEDyet. R3NOTpackaged; clonecorrectR2packagerR3paths,resourceSTORED andparentAndroidt0..679codec retained. R2immutableoutputsource-build-receipt.json+renderer-source-v036-r2.zip preserved.

TOPSKY unresolved: extraSouth431642sourceleaf198 D2416762614/nativeclear; strictsource/alias/boundscenterLODfilters preserveonly31/33nativeleafdraws andWITHHELD. SixcachedSPACEevent/lifecyclebodies, noDBimport; native-space-visibility/REPORT.md seedsmanager+b8/bc handlearray, notactivation/LODconsumer. ShadowproxyfixdoesNOTclaimtopcoveragefixed. Godrayshader/alpha/depth exact; emitterdimensioninput/signcandidatequalified. Waterfallstyleintentionallypreferredandunchanged. ContinueR3devicebatch, restorestate, Windows tasknormal--scene town, updateHANDOFF/CURRENT_STATE/README/privatebackup.

Notesrecovery: Windowsdefaultcp1252writerfailedonarrowandtruncatedledger; allFOURprevioussuccessfulwritesrecoveredfromrecordedcommandsbySAFEstaticASTliteral/concatenationevaluationwithEXACTread/writeencoding+WindowsCRLFsimulation. No research/shellcommandsrerun. ExactoldfilebytespreservedinNIGHT_CONTINUATION.before-encoding-error.md andreceipt; currentledgerusesexplicitUTF8. AlwayswriteUTF8viaatomictemp replacementfromnowon. No source,assets,builds,savesorresearchresults lost.

---

# Active final review: builds pass; no Android install yet

Source-proven native godray UV V sign corrected (native P1->P2=5000*V mapsv0->v1; quad topUV0 nowgeometry-V). Win/ARM final build passed; receipt pinned. ActualWindowsGL reports12native/12soft/12shaped withdepthsnapshot1 and no shadererrors. Candidate emitter shape remains partlypolicy, not fullydecodedproducer.

Three vertical thirds saved final-band-review/top.png,middle.png,bottom.png and viewed. Region tree poses97/97 found; reverse sky-opening check has9regional records and ALL9have native capturedgeometry witnesses includingmountain2061/draw68228. Current remaining top sky opening difference now being audited asmaterial/alpha, not guessed extra tree. Bottom foreground dark rock at50,735/100,725 is nativeFAB424996for_rock_stone05/draw69783VS923PS924; bounded agent comparing current source. Main root/lamp/cart fixes retained.

Initialv036APK built/signed/certverified but NOTinstalled: broad WindowsCRC scan also selected existing Android compressedtextures vsWindowsRGBA copies. Initial artifact preserved inoutputs/scene-v45. Corrected package_android_v036_r1.py preserves parentAndroidt0..679 codec/residency, only explicit680+texture corrections/newassets. Pending remaining material audits and finalsource pin before r1singledeviceinstall. No save/settings changed.

---

# Latest: nativeFXshader/texture integrated, shape candidate awaiting runtime review

CurrentWindows/ARMsourcecompiledsuccessfullywithoa_fx.c/hoptionalOATXoverrides/nativeprofiles/softdepth/UNORM8. TwoFXsidecars deployed, ORIGINALfx/fx.bin unchanged30cec6a2... . NativeFXprofiles6/27same4093/363355soft-additive; texture5nowexactauthored128²6mips instead32²runtime-generated. NativepayloadNF7exactshader/texture;type27NF127containsseparableSOURCE/OBSERVEDshapePOLICY: half550x2500, cylindricalvelocityaxisQconj andsourceMinMaxAngle5/5; zero-inputdimensionfallback+velocitysignpolicyareNOTfullydecodedoriginalproducer. debug.opem.fxshape0legacy vs1candidate LIVE withFXreset. Windowsstartupset0forcomparison. See native-fx-stage/manifest.json and transparency-audit/NATIVE_PRODUCER_REPORT.md (8-functioncapstopped; no false10/2angle,10isFlatness).

Newshadercompile/linkerrors explicitlyrefused/logged; alpha/colorlastkeyOOB corrected andLCGunsignedwrapdefined. Sourcevariables/fxShape nowreadliveperframe. Stabledepthcopiedprewater reusesopaque_depth; nativewaterandalllatertransdepthwriteOFF. Reviewstaticpassed beforeminorcompile/linkguards. NeedactualGLshader/profile/runtime/shapeA/B andfinalsnapshot beforeAPK. Sourcefinal-renderer-build.json UPDATED afterthisbatch, allWin/ARMexit0. APKscriptallASSETSCRCscanningnowincludesFXsidecars; v036package NOTBUILT/INSTALLEDyet. Tablet272B save/settingsbackup/rootreadalreadyverified; asleepnonsecurekeyguard, canwake/dismissfortestwithoutasking.

---

# Latest integrated continuation (supersedes intermediate notes below)

Windows now visibly renders restored Regiontrees, bridge lamp, wooden cart and mossyroot. BothWindows/ARM builds passed for geometry/materialintegration. Live world materialcount300/native41accepted;1336cells (65aux-only),202registryrows (201geometry+1leaf-bounds-only),175nativeleafcells. Fullyloaded reference stats2159draws/812399triangles,119regioncells/391regiondraws,queue0. These are WINDOWSsubmitted counts, not AndroidFPS. Screenshotbridge-point-phase-1-cart-native.png.

Sourcepack155regionalphysicalplacements/all51previouslyunmatchedcapturedposes EXACTsource/nativeTRS,97draws. Per-recordLOD(.5REGION provisionalcapturepreset,1.0actors), zeroSpace/Regionphysicalduplicates. Lamp14sourceactors, cartsourceactor+FABlocaloffset, rootsourceonlynearLOD/directTRS. Newnativeemissivefamily8/carfresnel9shader+authoredmips/probe3594; usesnewindependentoa_cart_probe.c/h WITHOUTwater.c/.h edits. Sourcefamily8review+family9SSA512case validation retained. MATSrows0..295 preserved; new296/297dot3alpha,298emissive,299cart. Runtimefield/phase3grass andexpandedboundsloadingreviewbugs fixed beforedeployment.

Spaceleaftransformguard: FULL78changed-source candidate NOTpromoted.49exceededoldbounds,73lacknativewitnesses, max100m. ONLY5native-sameassembly-proven records457/458/467/468/484 promoted:331triangles,6leafcells; allotherbytefields/triangles retained, one0.134cmunionexpansion. Keep73unobserved untouched pendingproducer/bindsemantics. Allcandidates/backups preserved.

NativeDOFphase recoveredanddefault1usesexplicitupper-left2x2 sampling (debug.opem.dofphase0legacy). WithcorrectRegiondepth, native800halfCoCquad51/34/51/18 andeffectalpha29 nowmatch; full3sampleDOFalphas29/94/43matchnative. DOF800RGB40,35,23 vsnative40,37,23. Final80032,28,19 vsnative35,32,20 (baseline136,123,50). Primary+fog98071,66,33 isEXACTnative afterverifiedleafshift. Remainingdarknessmostlytranslucentparticle/bloomfield, NOT primarylighttint. NativeG2alphasâ‰¤.4375doNOTselectwrappedlighting (.5threshold); omissionnotcause. Firstphase0labelledABimageactuallyusedstartupdefault1; invalidatedinpoint-phase-early-label-correction.json. SourceNOWreadsnewregion/dofphasepropsliveandlogsactualrenderphase, awaitingnextbatchbuild (currentbinarybeforethatminorhook).

ACTIVE nextfocus: nativephase111additiveforegroundmistPS1042draw73194 contributesallthreepixels. Nativeaftertrans98077,77,41 vsours68,63,34. CurrentSTATICveilMATS113â€“117arewebs: DO NOTblanketmakephase6additive. Existingoa_fxalreadyhasSRC_ALPHA/ONE foradditive types; needparticletexture/material/emitterdata+GREENalpha/depth-softnessjoin. Lightingagentinvestigatingboundedsourceproducer. No RGBeyetuning. Waterfallsremainowner-preferredintentionaldifference, unchangedwatermodule/pack.

Android remainsv035R4/code37, noinstallchanged. Tablet99cc517aconnected, insecurekeyguardasleep;rootreadworks. BeforedataalreadybackedupMacandroid-validation/before/app-files.tar,2files272B; save/settingsSHAunchanged. v036/code38manifestcompiledinwork/v45-apk. package_android_v036.py stagedbutNOTexecuted; checksfullsourcehashreceipt andautoCRCscansallworldassetdeltasbeforeincrementalZIPcopy/samekeysign. Needfinalbatchbuildreceiptrefreshedafterlivereadsourceedits/nextFXfix, oneAPKpackage/install/test. SigningkeyWindows-only. CurrentWindowsreferenceappopen, propertiesmaterialprobe0/dofphase1, taskreferencemode. Continuewithoutpermission/checkpointstop; nooriginalgame/Steamlaunch.

---

# Active overnight continuation, 2026-11-06

Owner: continue autonomously foliage brightness -> missing-tree gap -> top/middle/bottom thirds of matched original scene. Address missing bridge-side objects and mossy water roots. Waterfalls are deliberately preferred as currently rendered: no waterfall shader/material/geometry changes. Windows first, batch Android.

## Completed evidence and active changes

- Native leaf attributes expanded18->175cells/51,831existing leaf triangles in optional l*.bin stream (8MB); native shader normals fixed. No invented instances. Windows pixel error improved222->82 at800,150, but final brightness still differs.
- Isolated GFXReconstruct1.0.5 Windows replayer built from existing source. Two bounded static replays succeeded;15main stages(157MiB) and9DOF/bloomstages(14.95MB). Original game/Steam not launched. Exact native postfog800=(34,29,18), matching custom; major residual arisesaftertransparency/DOF/bloom. Current neighbor depth field differs due missinggeometry; DOFsampling/quad experiments were not cures. Highp depth sampler is retained as supported precision correction; baseline texelFetch sampling restored. All experimental sources/logs preserved.
- All51previously unknown native treeposes/97draws recovered EXACTLY from431608.region_bxml. Generic same nativeFabInstanceCollection reader is used bybothRegionandSpace; importer only emittedSpace. FourRegion refslots140/148/150/158, physics160/170/180/190(80B), render168/178/188/198(84B), refs16B FAB@8. Native97rawT exact/basis<.001. Newauxsource producer underinstance-audit/tree-gap-producer; not live yet.
- RootFAB359268 source-only directTRS/native nearasm0 correction promoted ONLYc1_-13_0.bin (root-deployment.json). Removes165wrongcachedLODtri, adds366native-source triangles; other52,815triangles preserved. Centered-scale oldrecipe shiftedroot2.435m. Nativepose/sourceT exact. Green coverage visually improved in moss-root-original-before-after.png. Family3shader now passesrawinterpolatedN/T/B before finalnormal normalization, perPS904. Source/roottexturesstill1024vsnative2048; broaderfidelitynotcertified.
- Missingleftobject is638222for_cart_overturned. SourceVB/IBmatchnative68274 EXACTLY. Sourceactor0x98(row0) plusactualFABlocalZ13.33494854 reproducesnativeT exactly; semanticbindownershipstillnotfullydecoded. Candidateprivate source geometry ready, row10legacyfresnelmaterial approximate. Notliveyet.
- Missingrightbridge lamp540961 issourceactor0x98(row17), T/Q/scale EXACTnative. Source14actors in visiblecells, allauthoredLODgroups available. Stageinprogress, newemissiveMID654012 needsrow298/nativefamilycontract. Genericactorcollection missingfromoldstaticimporter.

## Runtime working state (not release)

Sharedsource work/v19-host. Windowsapp source work/v40-windows-host. NewoptionalREGIONslot5 reader + authoredperdrawLOD metadata compiled once; source now additionallyhasper-rangeLODdistancefactor and independent alpha-map/cull handling, pending nextbatchcompile. Currentbaseworldcells unchanged exceptrootcell; leaftexturesfourcapture-residency substitutions. No live region-index yet, regionstats0.

Auxformat OARGEO1+NUL magic8; u32vertexCount,indexCount,drawCount,vertexStride76,rangeStride48; then48B <4I6fIf>: materialRow,firstIndex,indexCount,rawFlags,LODanchor(rawT.xyz),boundRadius,minSq,maxSq,sourceIndex,floatdistanceScale(0usesregistry). ThenOAWE76vertices/u32indices. RegistryOARGIDX1 magic8,u32cells,u32materialCount,floatdefaultScale,u32reserved0;40B rows i32cx,cy,u32tris,u32draws,float6actualbounds. Regiondefaultscale0.5isPROVISIONAL captured-qualitypreset (97/97observeddrawintervals), exact native globalfactorunresolved. Actorperrange1.0validatedsourcegroups at2nativeposes. NeveremitallauthoredLODs atonce.

Reservednewrows296=343630treebarkbonus(dot3alpha),297=1611839skyline(dot3alpha),298=654012lampemissive. Finalmaterialcount299mustmatchMATS/nativeprofiles/leaf-index/region-index. ReservedtextureIDs685..692for2dot3alpha profiles'8source maps;693..696forlampifneeded. Preservealloriginalprefixbytes/assets andbackups. REGIONALnewleavesdrawintheirauxstream, notoldleafsidecar,torespectauthoredranges.

Android remains v0.35R4/code37, save/settings unchanged; tabletADB99cc517avisible. No v45APK packaged/installed. Do NOT claim newer Androidperformance. ReferenceWindowsapp currentlyruns withlive255/shadows1/normalLODs; tasktemporarilyreference scene. Diagnostic debug.opem.materialprobe=0 (desktop-only smallreadbacks perstablechange). Closeownappbeforeasset/exe changes; restoretasktownmodeatend. Originalengine/FEX workpaused. Signingkey/PCsaves/databases untouched.

## Next concrete work

Finish2nativeDot3Alpha materialstages/Region61MBgeometry+LODpack; mergeactorlamp/cart sources; verifyoptionalstream withnative97treecoverage andmatchedimage. Inspecttop/middle/bottomcrops. ReevaluateDOF/bloomusingcorrectdepthfieldbeforeanyretuning. BatchWindows+ARMbuild, packageoneAndroidupdatewithnewassets and existingkey; verify save/settings andnewstream/walking/lifecycle ontablet. Preservewaterfallfiles byte-identical.
