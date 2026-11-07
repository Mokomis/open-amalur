# Active ambient cube runtime identity: R/B mismatch found

2026-11-05 static capture/source investigation. New files only, no shared edits or runtime/UI operations. Original recording SHA72c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209.

## Concrete correction

Current outdoor opem_town_cube upload is channel-swapped relative to the actual native runtime cube. Swap R/B in the OUTDOOR upload preparation, leaving green, alpha, face order, rows and sampling direction unchanged. The provided source-pixel helper is safe in place and does no colour-space conversion. This correction is specific to the proven current outdoor cube source; indoor cubes/unrelated assets were not audited.

This is a byte identity result, not visual tuning. All6faces/1536bytes of original runtime pixels equal current authored arrays ONLY after R/B swap. Without it754 channel bytes differ, maximum channel difference50. Original first texel is(48,48,34,255), current(34,48,48,255). Original tight SHA256df71f39a8cfa77673155c7ec5d5de4b3d36583c05c712ac9022e920c96fcef1c.

## Active resource and packing proof

Main active ambient cube is view7498/image7496,8x8, six layers, one mip, VK_R8G8B8A8_UNORM. View typeCUBE, identity component swizzles, layers0..5. It is not a1x1 fallback, sRGB view, different-size generatedSH approximation or another authored Noon cube.

Original InitImage block18222 at byte125411374 records3072payload bytes for this one mip. Existing official VulkanReplayConsumerBase::ProcessInitImageCommand constructs ONE copy region per mip with bufferRowLength0, bufferImageHeight0, baseArrayLayer0 and layerCount6. Thus the six8x8RGBA layers are contiguous first1536bytes; the remaining1536bytes are end-of-level allocation padding. A guessed512byte stride per face reads padding and fails identity. Raw full payload and tight pixels are both retained.

The current6x256byte arrays were parsed directly from current work/v19-host/town_environment.inc; room_lighting.c passes them as GL_RGBA to GL_RGBA8. Original captured bytes are interpreted as RGBA by an identity-swizzle RGBA view. Therefore preserving the source converter's current R/B swap does not reproduce the active original runtime resource.

All six faces match individually with only a channel swap, so no face permutation, row flip or per-face rotation is needed in the uploaded bytes. Layer order is cube+X,-X,+Y,-Y,+Z,-Z. Active material shaders sample ambient at N.xzy, matching the current shared world helper. For worldZ-up, (0,0,1) selects cube+Y; preserve this direction swizzle. Cube sampling face coordinates use the usual major-axis mapping; changing data orientation as well as swapping channels would break the proven correspondence.

Native sampler336 is LINEAR min/mag, linear mip selection, clampU/V, no anisotropy, mip range0..1000. There is only one exposed mip, so currentGL_LINEAR filtering is equivalent for available levels. Native samplerW isREPEAT but the third cube direction component is not a conventionalW-wrap coordinate, so the currentR-clamp does not create a volume-texture wrap difference. ES3 cube filtering is seamless; a desktop compatibility path should keep equivalent cube edge filtering. This audit does not claim native GPU readback of the custom upload; root owns the runtime check.

cube-validation.json preserves full image/view/sampler definitions, source/current hashes, exact comparison and six centre sample values. The fixture tight pixels are diagnostic evidence; the portable correction uses the same authored source with the channel conversion fixed, with no scene/save matching condition.
