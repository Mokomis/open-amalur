# Performance gate completed — November 5

Read ../open-amalur-performance-check/RESULTS.md. Fresh native workload: 31.14 FPS at 1536x864, 750 timed frames; CPU profile 44.76% driver and 31.99% replay library. Rough full-native planning estimate 30–45 FPS, heavy/heat 20–30, optimistic light/optimized 45–60; these are judgments, not measured gameplay. Stable30 is a plausible first target; no 60FPS guarantee or measured FEX percentage. Fresh FEX gameplay not obtained: Steam opened but two input methods did not advance the game tile; no repeated launch investigation. Windows8second CPU sample unpause not verified, final screenshot paused. Tablet left inSteam, native app not running. Details/evidence on both hosts under v38-performance-check. User wants substantive progress and bounded measurements; do not repeat this check without a new reason.

# Latest owner priority: performance feasibility gate

Read PERFORMANCE_FINDINGS.md first. Owner asks for an educated Android FPS range and single/multicore architecture. Confirmedstatic4-workerJobMgr setup at0x00b05f10; shortpausedWindowsCPUcheck showsmain/renderdominate,butdoesnotestablishfullgameparallelism. Nativecharacterfeatureisnowsecondarytohotpath/translationcostprofiling. Tabletlastseen asleep,viewerpaused/focuslostandprocessnotpresent;APKv11remainsinstalled. Do notunnecessarilywake/relaunchforstatusquestions. No60FPSpromisefromcapturereplay.

# v37 native character path — 2026-11-05

Read canonical AGENTS, then this file. Windows authoritative work/v37-native-character; Mac folder open-amalur-native-character. Original executable, tools, frozenengine, APKs, saves, keys allpreserved. No reinstall/reset, no GitHubpush. Sol High, noAstra orQwenused.

## Verified milestone
VersionCode11/versionName0.11-native-character installed ONLYorg.openamalur.nativebenchmark withsamebenchmark key. 222-step buildpassed, APKverified. Seev11-build-info.json forhashes. ARM64 native bridge uses recoveredkind0one draw, kind1fourenvironmentdraws, kind1fourlargercharacterdraws =9drawgeometrytails perframe. Most rendering/state isstillcaptured. Nativeengine notcomplete/playable.

Evidence/validation-summary.json: originalpalette runnative-character-v11-zero-30 first/last/rawRGBbit-identical1536x864; alternate recordedpalette runnative-character-v11-palette1-30 first==last,12216RGBchannels differfromraw withinx412..687,y341..699, visiblyonplayercharacter. Each30frame run:120characterkind1replacements,120firstkind1,30kind0;0rejections. DoNOTclaim nativeanimation generation: two recordedposes only. Sourcepalette1200bytescount25matchesactualVS5bufferbyte-for-byte. Shared68stride1456verticesindices0..24. Draws66652/67627/72229/72628 uniquelyresolvedbycompletevertex+indexcontent despiteone duplicatevertexbuffer. Seecharacter-evidence.json andnative-resource-bridge.json. Originalcodeentry snapshots preserved; no speculativefields substituted.

Viewer restored liveatuserposeyaw0.14175,pitch0.089045,right/forward0,palette0. Privateactive logfiles/native-character-live/replay.log. Launcherfromv36 supports --engine-geometry --palette 0|1. Touchcamera stillavailable. NoFPS/FEXoverheadclaimfromshortscreenshotchecks.

## Upstream native evidence
CapturedoriginalpacketbuilderVA0x00cb64c0,relocated0x010664c0,callerVA0x00cd40d8inside0x00cd3ea0. Actualowner0x25f123a0: transformstart+0;sourcepointer+0x30=>0x3d4c4de0,count+0x34=25. Sourcepoints1200bytesconsumedbyshader. Builderreturnsdifferentallocatedpacket0x2d877550withsamegeometry0x065dd1c0,count25/sourceexact. Inputs+resultin capture-2026-11-05T21-26-15-815Z; earliertrace21-20-39retained. Bothbounded<300msanddetached.

Portableoa_packet_builder.c recoverspositive-countskinnedpacketTAIL ONLY. Takesallocationconstantblocktoken asinput; excludesarenaallocation/locks,matrixgeneration,andkind0/negativebranches. MacASan/UBSan:all56nativeoutputbytesmatch,3negativechecks. NotARMvalidatedorintegratedyet;donotclaimfullfunctionport. Sourcesand1044bytefixturepacket-builder-real.binpresent. Runtimepacketexpecteddirectoriginaloutput,separatefromimplementation.

Writerwatchcapture21-30-01:39existingthreadsfirst4byteswritewatch1200ms,nowriteobservedwhilepaused,cleanupunsetanddetached. Paletteunchangedbetweentwoearlierpausedcaptures. No broadnowriterclaim. Do not repeatpausedwritewatchunchanged. NoPCgameplayinputs sentduringthesechecks.

## Latest steering: accelerate substantive native work
Owner saysprogressslow. Stopaddingcaptured-drawsubstitutions asprimarymilestones. Nextfeature:onecharacterloadedfromgameassets,originalanimationdecodeportedARM,posesgeneratedatruntimeandoriginalVulkanshaderused. SeeNEXT_NATIVE_FEATURE.md. Batchbuilds/testingpercompletefeature,retainnecessarynativeaccuracychecks. NoadditionalAPKbuildforpacketheaderonly.

Existingv19/v20characterworkisSALVAGE: sourceoa_character.h explicitlysaysofflinebakednativeEdgedecoderoutputandAUTHOREDpreviewassembly/blending. DoNOTshipthatpreviewpolicyasrecoveredengine. Existingv20-char/clip_bake.cpp andclip-bake.exe provideoriginalx86oracleatVA0x0111bf10; no needreinstallorredo. Existingrawclips/skelavailablev20-inputs. decomp_bf10.txt anddecomp_channels.txt retained. Candidate0x00c87130wasdiscarded:shaderloader,notpalettewriter. Broadownerfieldscan44candidateswasnotproof;avoidchasingbyoffsetalone.
