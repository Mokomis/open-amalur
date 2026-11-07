# Next native feature: original animation from assets

Visible acceptance target: one real character plays an idle clip generated on ARM64 from the game's compressed animation asset, using the current original translated Vulkan shaders. No x86 animation code or recorded pose sequence drives the tablet feature. Keep current scene viewer working throughout.

Reuse first:
- Windows work/v20-char/clip_bake.cpp + clip-bake.exe: isolated original x86 decoder0x0111bf10. Reference oracle only, no game entrypoint/device startup. Inputs:koa.exe, skeleton.fab_bxml, clip.anm_bxml, output.bin. Existing executable and baked results retained.
- work/v20-inputs: already-extracted game assets and symbols.json; work/v07-mesh/amalur_mesh.py + relatedv07BXML parsing; existingarchiveindexes. Scanselectedformats ratherthanreextractingarchives.
- work/v20-char/decomp_bf10.txt (~7KB dispatch) + decomp_channels.txt (~64KB), andcurrentv30Ghidraexport/machineinstructions.
- Frozenv19oa_character.c/h: reviewassetdata/quaternion/palettehelpersforsalvageONLY. Headersstatepartselection/blendingishostpolicyandposeswerebakedoffline. Do notreactivatethefrozenrendererorcallpreviewpolicyoriginalengine.

Batch:
1. Chooseexisting64-joint human_idle_01clip fromsymbols; inspectactualflags/counts toselectrequireddecoderbranches. Existingfirst16clipinventoryshowsflag0butdifferentrigs;notselectionproof.
2. Recoveronlyrequirednativechanneldecoder+dispatch pathfrom0x0111bf10. CollectoracleoutputwholeclipatonceandcompareARMresultsatbatchend. Includefractionaltimebeforeclaimingcontinuousruntimeplayback. PreserveSSEprecisiondetails;don'tcodefromgarbledSIMDpseudocodealone.
3. Connectskeletonhierarchy/inversebindpalettemappingandrealmeshassettooriginalVulkaninputs. Current9drawbridgeisthestagingrenderer,notthefinalengine. Matchassetidentitiesproperly;firstboundedscanof649v20-inputsFABcontrolfilesfoundnoexact10752byteindexpayload--theseareoftencontrolrecords,needmeshparser'sactualstreamformat.
4. OnecombinedARMbuildandtabletcheckaftercompletefeature. Reportvisibleanimation,originaloutputcomparison,andremaininggaps. Noarbitraryframe/poseinterpolationclaim.

BoundedRErule:aftertwoattemptsattheunchangedblocker,changemethodorflagthepreciseunknown. NoAstrawithoutownerapproval. Solretainsimplementation/review. OptionalQwenonlynarrowindependentstaticfactswithrawevidencereview;do notaddmodelstartupoverheadmechanically.
