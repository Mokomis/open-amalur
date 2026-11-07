# Foreground rock directional-shadow audit

The native rock is fully sunlit at both requested pixels. This is now supported by actual native D16 depth comparisons, independently of the earlier AO image interpretation.

Dump66901 is the AO bilateral completion before native shadow geometry/resolves, so its G=1 is initialization and cannot by itself prove final sun visibility. Existing native far/middle/near shadow dumps and captured PS1900 resolve constants close that gap: middle-cascade alpha=1, near/far alpha=0, and all four middle bilinear comparisons pass at both pixels. Native finalG reconstructs to1.

At(50,735), linearZ=502.8595, receiverQ=(.89050645,.40875459,.99051619). Native middle taps x911/912,y418/419 allD16=64923. At(100,725), Z=517.9482,Q=(.88256103,.40757993,.99053222); tapsx903/904,y416/417 are64925/64924. GL raw-storageY is1023-nativeY. Native-shadow-tap-samples.json includes exactweights, constants, rawdump hashes and every tap.

## Projection and cascade contract

Current construction at the native-reference camera agrees with native middle receiverQ within9e-6UV and6.3e-8depth: less than.01maptexel and far smaller than the roughly9.5D16-unit visibility margin. It uses the correct active middle range440..1500, overlap100, receiverbias-.00015, D3D0..1depth reconstruction, single GLclipZ remap and one textureY flip. Both current/native alpha decisions select only middle here.

A known near-cascade FOV/snap difference of roughly one maptexel remains when deriving projection scales from rotated floatVP; its alpha is0 at these pixels, so it cannot cause this foreground shadow. No concrete cascade/projection/clip/UV bug explaining the current dark result was found. Comparison is a static reconstruction of current source at the known native camera, not a new runtime matrix readback.

## Concrete precision-contract gap

Current resolve shader declares scene_depth as an unqualified sampler2D, while only sampler2DShadow has a highp default. Native PS1900 has no RelaxedPrecision decorations. Private GLES310-equivalent glslang inspection gives four RelaxedPrecision decorations on current scene_depth/sample results; adding only explicit highp to that sampler removes allfour. See precision-check.json and paired disassemblies. Parent can use uniform highp sampler2D scene_depth. This is an evidenced portable precision correction, not proof that it causes the current Windows image difference.

## Caster cause remains bounded

Current G=0 versus reconstructed nativeG=1 could come from extra/wrong caster coverage, caster material/alpha/deformation, or a current map/sampling difference. The proposed inactive South-space caster explanation is plausible but not causally proven here: no current middle-map raw values or occluding source triangle were supplied. No bias/tint adjustment is supported. A current middlemap footprint comparison is decisive: GLx911/912,y604/605 expects all64923; GLx903/904,y606 expects64924 andy607expects64925. Unexpectedly closer currentdepth establishes a caster-side difference; matching depths points back to resolve/state/precision.

This audit used only current source, saved native constants/shaders and the three existing native depth dumps. No native bodies, game launch, replay, core/live asset edits or bias tuning occurred. Private shader compilation was static only.
