# Default Varani male preview audit

Staging only: C:\Users\rwill\Documents\Opem Amalur\work\v49-character-create\varani-preview-audit.
No live/core/default/preview/user files, source archives, oldpacks, DBs, saves, originalgame/UI orMac mirrors changed. Existing exporters/verifiers were adapted only inside this newfolder; no shader/native-function investigations repeated.

## Ready for root integration

corrected/character.bin:
13,629,260B; SHA256 a3454f607a2245dc8d70a580e09d5d9c2e701133301cfaa8bed87f5009ce1a06.
OACHAR01 header64joints,30clips,16parts,15textures.
Only40,839bytes change, entirely within normalXYZ@12..23 of the existing52B appearancevertices. No resize or otherfieldchange.
Allpackheaders,rig/parents,clips,textures,palettes,positions,UVs,joints,weights,indices/order and5rigidweapon attachments remain byte-identical.

Original source pack stays13,629,260B SHA0c9452b0ee5412e8066f830020ccdda2cf28bd7be1539c88d37a8b453bf901e2.

Optional alternative:
varani-male-attributes.oacat,950,060B SHAa54f087f1f3286ecf4d8f5d865209a5dd43780c4e8d0fb0ad8a264b1e2b7c22d.
This exact packed TBN/UV0/UV1/RGBA companion binds ORIGINAL packSHA above, NOT the correctedpack. Choose either original+companion or correctedpack; do not mix theirbaseidentity.
Sourceattrs cover11appearanceparts/7688vertices/32634indices. Absent stream1fields are explicitlyabsent, not inventedwhite/UV.
The64B zero-record varani-male-palette-corrections.oacpl is an auditartifact only; no runtimepalettecorrection is needed.

## Actual defect

The oldbuilder's normal-length scorer chose sourceTANGENT instead of NORMAL for3536vertices:
-hands part0/FAB514034:1086;
-legs part2/FAB1318954:1104;
-torso-skin part3/FAB1318955:99;
-eyes part7/FAB1362163:209;
-mainbeard part9/FAB1293355:1038.
Normals now decode exact sourceSNORM16 xyz at native declaration offsets32 or40 bystride/type, with no normal-length heuristic or renormalization.

## Default source selection

Recovered CharacterData751829 SHAa7a3739dcf1830095983e123adc9bc20358aa2eedd53116bdf6798784beafec3 sets m_default_customization (SETGLOBAL pc6330/file25617).
Varani_Male creatorType1536821 uses commonrigFAB456813; source fullplayerType669805.
DefaultHead1304403->FAB1362163,Hair1304591->FAB1302013,Beard1389483->FAB1293355 exactly match packrecipe andactualbundlehashes.
Source defaultSkinTone2,EyeColor5,HairColor4,BeardColor4 are preserved asmetadata; thispackdoesnot apply the fullsourcecosmeticcolor/mask/morphpath.
creation-default-proof.json links scriptprovenance,source tables/catalogue,all3bundlehashes andselectedmeshes.
This proves defaultgeometryselection, NOT fulloriginalpresetappearance.

## Palettes and rigid conventions

All125source palette slots across11assemblies match their OWN assembly's descriptor count+bonehash/ancestorassociation.
Independent scalar quaternionmath reconstructs all existing32B inverse-common-rest entries byte-exact. No palette/rigidbind changes are staged.
No Almain-shirt-style wrong-table association was found.
Facial/beard helperbones absent current64rig still use the existing ancestorpolicy(50slots). Source remap offsets/Q/T are preserved inweights-and-palettes.json; large facialsource-vs-common inverse differences remain thatknownapproximation, not a new correctednativefullfaceclaim.
Existing proven weight policy remains unchanged;250vertices have tiny negative nativefourth residuals that oldbuilderclamps. No weight tuning.
Five rigidweapon attachments remain exact originalbytes and outside thisappearancecorrection scope.

## Verification and limitations

Independent OACAT source validator:PASS11parts,44 malformed/wrong-base cases rejected.
Independent correctedpack verifier uses separate stdlib skeleton/quaternion/sourceoffset reconstruction; everybyteoutside normalXYZ allowlist remains exact. Alloldpaletteentries byte-match independently computedexistingcommonrig inverse-rest.
Originalpack/source hashes rechecked after staging.
No GPU/render/animation test in thisscope; rootowns previewruntime.
Olddiffuse-only textures,fullskin/hair/beard cosmeticcolors/masks,morphs,missingeye-shadow/mouth-black surfaces,sourcefacialauxiliaryrig andexactoriginalcreatoridle remain unimplemented/qualified. Base-modelpreview /Colourpreviewpending is the supported claim.

delivery.json is the short integration receipt; independent-pack-validation.json and validation-receipt.json contain checks; source-join-manifest.json and weights-and-palettes.json containper-part evidence.
