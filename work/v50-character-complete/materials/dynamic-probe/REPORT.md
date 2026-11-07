# Native dynamic environment probe: creator fallback resolved

The original renderer uses a scene/configuration query, not material slot21 and not the main/character ambient cube. This report is static native evidence plus existing original-frame resources; no game execution or database change.

00d1ad60 publishes each source Space probe collection:20-byte source record contains positionXYZ at0, source texture resource at+16; native arrays become Vec3[count] at object+4/count+8 and backend texture resources at+20/count+24. The object is queued through command0x28, handle+4 and RenderConfig handle+8. The exact source Space payload probe array at+0xf0 is confirmed by the parent source/assembly audit; creator Space1583581 count0.

00d42f40 command0x28 obtains the collection from backend+0x644[handle&0xffff] and appends it to RenderConfig+0x28 pointer array, count+0x2c.

00c97e90 resolves each query XYZ across every registered collection. Initial result is RenderConfig+0x14. Initial squared distance is the exact constant atVA013be4a8 (receipt query-distance-initializer.json). Distances are ordinary3D squared Euclidean; strict less-than preserves the first encountered point on ties. It selects the parallel texture-resource array entry. There is no camera-depth metric, weighted probe blend, nearest-world-material substitution, or per-space limit in this query. With no points the result remains RenderConfig+0x14.

00d32700 creates the main and auxiliary RenderConfigs. It resolves TextureMgr global DAT019fe000 member+0xf0 through00a71e80, obtains texture object's backend resource+8, and assigns that to each RenderConfig+0x14.

00d33b10 identifies DAT019fe000 as TextureMgr and initializes its fallback members. 00cbc310 creates SimpleBlackCube by calling00cbc180 with format0x8000, cube flag0x40, dimensions4x4, colorDWORD0, and stores its handle atTextureMgr+0xf0. 00d35760 RenderIOGlobals initialization calls00cbc310 before render-system setup. The helper00cbc180 fills the allocated texture data with the requested DWORD, including all six cube faces. Its decompiler signature is damaged, but the caller arguments and member store are explicit; zero is independent of channel ordering/padding.

Therefore the source-supported creator input is an owned4x4x6 all-zero RGBA cube passed as a borrowed texture through oa_cm_environment_probe. The parent owns creation/upload/lifetime. This is an actual native procedural fallback, not an authored-cube guess. No material implementation changes are needed.

Source2036011 named default_cubemap was independently extracted and rejected as active Gorhart probe3574: none of36face/mip blocks match. This does not affect the now-proved procedural no-point creator fallback. Gorhart3574 is an actual spatially selected probe and remains a different resource.

Original CharacterReflect VS381 multiplies global environmentTint.rgb (binding65 row6) by instance buffer binding67 row3 into outputLocation5. Active instance67543 is all-ones default, not selected eye colors. The customizable shader updater00dda730 does not include source shader545211; do not feed creator EyeColor into this noncustomizable default instance. Material TintColor@64 is declared but not read by this optimized VS/PS pair. PS382/retained7d82d59d56cb0f69 adds mask.GREEN times probe(reflect(-V,mappedN).xzy) times that interpolated tint inside G2 clamp/F16. All three required default LjosalfarFemale source materials have authored white TintColor, preserved in the raw catalogue.

Remaining scope: this pass resolves the creator/no-point case and native general query math. Populating and maintaining all gameplay Space probe collections while moving between spaces is parent runtime work, not implemented here.
