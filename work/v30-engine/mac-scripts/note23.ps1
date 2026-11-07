$note=@'

V0.20.0 (2026-10-31): versionCode 21, APK outputs/scene-v19/opem-amalur-scene-v0.20-arm64.apk sha256 starts 75869ea0d7c4121b. KEEN non-square textures stop at their declared mip count (keen_texture.parse rejected them; build_town.decode_best handles them; keen_texture.py itself is unchanged). Opacity comes from a separate _a texture; other stored alpha is forced opaque. Scene shader has alpha_cut, 0.5 outdoors, 0 in shop and on the character. Tree shadow proxies (material names with shadow, for_temp) are dropped. Ground texture by slope is an authored approximation. Workbench draw now uses texture 697080 through work/v20-town/scene_materials.bin; 4 other shop draws remain fallback and may be the same bug.
OPEN: paint maps (1344 records, 129x129 RGBA) are not in chunk order, no fixed offset correlated (best 0.153); the link needs native code from TerrainObject 0xd46f60 or shader terrainBlendTexcoordTransform. Palette file initial_0.pak 4720.palettetmp_bxml.
REFRESH: tablet display modes 60, 90, 120, 144; peak setting 144; no ANativeWindow_setFrameRate request yet; eglSwapInterval 1.
'@
Add-Content -Encoding UTF8 'work\CURRENT_STATE.txt' $note
Add-Content -Encoding UTF8 'outputs\scene-v19\PROGRESS.txt' $note
'noted'
