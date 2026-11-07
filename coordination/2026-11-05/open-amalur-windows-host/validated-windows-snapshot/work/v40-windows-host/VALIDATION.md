# Validation — 2026-11-05

Verified on ROBMACHINEX / RTX 4080 SUPER using the Windows host, not FEX:

- Windows executable links successfully; final build result 0 in final-build-status.json.
- Android ARM64 shared library compiles successfully; final build result 0. No APK built/installed this session.
- Python host/content utilities compile.
- Real custom runtime initializes Lua, 190 bootstrap modules and the Workbench service.
- Gorhart renders streamed geometry, textures, terrain, foliage, animated player and actors. GPU capture: evidence/gorhart-warm.png.
- E enters the shop: evidence/shop-first.png.
- W held 1000 ms moves feet from (-342.400,-139.600,0.250) to (-342.400,281.240,4.359), 4.2084 m horizontally, grounded, zero recoveries: evidence/shop-walk.png and saved host log.
- Shop/town movement and interaction above were checked before the final adapter/brace-only build. Final launcher smoke check is saved separately.
- Clean shutdown observed through the file queue. Audio mixer/device initialized; listening quality and triggers were not verified.
- Original-camera render: bridge-custom.bmp and metadata, matching original recorded view-projection matrix and eye position.
- Initial physical input adapter labels were replaced by virtual logical channels before final build.

This demonstrates a useful desktop development host, not full gameplay compatibility, complete quests, exact visual parity, or measured Android performance. Offscreen readback and pacing invalidate performance extrapolation. Desktop AAudio underrun counter is unsupported (-1); the existing unsigned log may print 4294967295 and must not be interpreted as a measurement.

Actor native-heading repair evidence is in ../v41-world-objects. All 91 placed actors matched uniquely; only 65 heading fields changed in the source and desktop indices. Positions/models and encounter actor records remain byte-identical.

Final start.py launcher verified through its interactive scheduled task; GPU capture evidence/town-final-build.png and camera JSON; runtime log evidence/final-launch.log. One startup GL_INVALID_OPERATION (0x502) occurred at frame 1, with no later GL errors in this capture run. Cause remains undiagnosed. Visible scene and runtime bootstrap still succeed.
