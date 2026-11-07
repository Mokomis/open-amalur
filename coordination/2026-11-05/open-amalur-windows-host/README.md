# Open Amalur Windows development milestone — 2026-11-05

The existing custom Android runtime now runs as a Windows scene preview. Textured Gorhart, shop transition and grounded walking were verified. Final Windows executable and Android shared-library builds pass. No tablet installation changed.

The authoritative source remains on ROBMACHINEX at `C:\Users\rwill\Documents\Opem Amalur`. `validated-windows-snapshot/` is a selective source/documentation snapshot for review, not a complete build backup; required private assets and existing outputs remain on Windows.

- [Run/build guide](validated-windows-snapshot/work/v40-windows-host/README.md)
- [Verification results and limitations](validated-windows-snapshot/work/v40-windows-host/VALIDATION.md)
- [Original-game footage workflow](validated-windows-snapshot/work/v40-windows-host/REFERENCE_VALIDATION.md)
- [Native object-record and actor-heading findings](validated-windows-snapshot/work/v41-world-objects/README.md)
- [Fresh Windows town capture](evidence/town-final-build.png)
- [Original recorded bridge view](evidence/bridge-original.png)
- [Custom-engine matched-camera view](evidence/bridge-custom.png)

Still-image comparison is established. Paired movement footage remains outstanding. Missing props, terrain paint, foliage, water, fog and lighting differences are real fidelity gaps. The desktop readback host is for correctness and is not an Android FPS estimate. One startup GL error is recorded. Native object-list decoding and the 65 actor-heading repairs do not constitute recovered original gameplay behavior.


## Native prop restoration

251 recorded crates, barrels and urns now appear in the Windows scene, using nine recovered models and three native materials. The bridge stacks match their original placements in the reference frame. [Updated capture](evidence/bridge-restored-props.png) and [implementation/evidence report](validated-windows-snapshot/work/v42-object-visuals/README.md).

This is visual restoration; destruction, loot and original physics remain unrecovered. A derived collision draft is saved but disabled because the real-terrain before/after crossing probe did not establish a valid comparison. Non-identity local bone transforms remain a bounded native-evidence gap. Existing world geometry, saves, keys and databases are preserved; no tablet update was performed.
