# v36 native ranged geometry and instance constants — 2026-11-05

VersionCode10 /versionName0.10-native-ranges installed inorg.openamalur.nativebenchmark. Source copiedv35 toseparate Windowswork/v36-native-ranges/src; build222stepspassed. Original app/key/save and all previous versions preserved.

Nativekind1geometry decoder follows original instructions at0xc96fd2..0xc970c4. Two138vertex resources and948byteindex buffer map exactly toVulkanVB7777/1831,IB7779 inimmutable frame50994. Fourdraws63022,65558,68129,68131. Recovered native geometry submission drives actual474index draw calls, preserving captured shader/material/pipeline state. Existingkind0 draw69921 remains active.

Tablet native-ranges-v10-zero-30:120kind1 replacements,30kind0replacements,0rejections;4palettecopies(count6*48bytes). First/last/rawRGB1536x864bit-identical. Portableconstantcopy also independentlymatches originalnativeCB5 output on MacASan/UBSan anddirectAndroidARM64;6negativeboundschecks,zerocountvalid.

Alternate recorded palette run native-ranges-v10-palette1-30: copylogconfirms pose1,120kind1 replacements/0rejections; first/last/rawRGBstillidentical. IMPORTANT: This mesh has not been shown to affect visible pixels atthiscamera; occlusion is a candidate, not established. Do not claim visible animation, alternateposevisualsuccess ornativeanimationproducer. All138verticesindices0..5 are inside6transformpalette. Livepose differs numericallyfromoldcapture. Shader577binding69 implementsweightedskinning.

Restored active viewer native-ranges-live atuserposeyaw0.14175,pitch0.089045,right/forward0,palette0. Actualcamera controls stillavailable. NoFPS claims for screenshot runs, noFEXoverhead estimate, nofullnativeengine claim. v37-next: bounded originalcase1 trace forlargermeshwith30..80transforms and>=3000indices, toreachclearlycontributingcharactergeometrybeforetransformproducerwork.

Windows: C:\Users\rwill\Documents\Opem Amalur\work\v36-native-ranges. Maclaunch: python3 oa-launch-native-ranges.py --name native-ranges-live --engine-geometry --palette0 --yaw0.14175 --pitch0.089045 (flags needspaces: --palette 0 --yaw 0.14175 --pitch 0.089045).
