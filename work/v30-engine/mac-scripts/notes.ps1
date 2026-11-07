$n=@'

v0.28.0 live-load results (2026-10-31, tablet native 2520x1680, Dalentarth, 932 real lights)
Changes: flora atlas opacity read from green channel, cards use one atlas plant (layer-to-plant mapping authored); per-tile light grid (8 m tiles, up to 8 lights, 3 of 9363 tile references dropped); shader variants opaque/terrain/cutout/foliage; draw order nearest first, buildings, terrain, cutouts, foliage; fog per vertex; mediump colour maths; scene target R11G11B10F.
Fixed views, uncapped, frame ms (GPU ms): base 4.76 (3.55); all lighting 6.31 (5.20); +shadows 9.01 (7.86); +crowd 60 10.25 (8.23); +fx 1500 11.49 (9.53). Headings 0/180/270 with shadows: 8.49, 7.98, 4.83. Before: 15.90-38.41.
Moving tour, crowd 60, fx 300, 1 km view, 7 m/s: uncapped 3 min mean 5.23, p95 7.47. Vsync 10 min p95 16.67, GPU mean 6.11, max 7.88. Battery 34.5-37.6 C. Android thermal status 2 uncapped, 0-1 vsync. PSS up to 561 MB.
Not in the load: real AI at scale, audio, water shader, real effects data, real NPC placement (crowd is proxy), 724 of 1720 unmatched veggie tiles, other zones. Tour path is not walking; it can place the camera in canopy.
'@
Add-Content -Path work\CURRENT_STATE.txt -Value $n
Add-Content -Path outputs\scene-v19\PROGRESS.txt -Value $n
"written"
