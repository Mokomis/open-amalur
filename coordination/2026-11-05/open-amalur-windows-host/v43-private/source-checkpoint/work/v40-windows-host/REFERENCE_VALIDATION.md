# Original-game reference workflow

Owner requirement: use footage from the actual game to assess placement, lighting, terrain, animation and movement. Original captures are the visual reference; decoded scene/native evidence should explain differences. Do not tune from memory or treat authored approximations as recovered behavior.

## First reproducible paired view

Original: work/v31-native-slice/render-20261105/windows-replay.png.
Camera: record 0 from work/v33-native-camera/shared-camera-records.json.
Custom: work/v40-windows-host/bridge-custom.bmp (+ JSON metadata).
Provenance: native-reference-provenance.json. Native source data stays private.

The flat 16-float D3D row-vector matrix is the GL column-major transpose. Only depth range is changed: for each column c, m[c*4+2] = 2*original[c*4+2] - original[c*4+3]. X/Y/W are unchanged. Exact original eye XYZ is used. Fixed camera hides the preview character and its shadow; it does not move or modify the original game or saves. Captured vertical field of view is about 46.44 degrees in this view; do not generalize it to every game camera.

## Observed gaps

Major bridge/tree/ruin geometry aligns. Missing clutter/props, approximate terrain painting, different foliage, water tint, fog and lighting are visible. Exact lighting is not established. The new native object-list parser is a recovered placement contract, not proof that every missing prop is now rendered.

## Continuing comparisons

1. Preserve original frame/short clip and scene/camera/time/weather provenance. Prefer existing reliable renderer recordings over stale desktop snapshots.
2. Match viewpoint, resolution and scene conditions. Check silhouettes/coordinates first, then materials/terrain, lighting/fog/water and finally motion.
3. Keep native decode facts separate from inferred settings and authored fallback choices. Record unknowns.
4. Save immutable comparison captures and a short issue list; fix shared loader/render behavior rather than manually moving each object to match an image.
5. Add paired movement clips to expose animation, collision, streaming and temporal-lighting differences. Only still-frame comparison has been completed so far.
6. Tablet validation follows substantial portable improvements or Android-specific questions; no installation after every small edit.

No save is required for every room to decode its records. A live original scene is useful for selected reference captures and runtime behavior. Original desktop snapshots appeared stale this session, so no original-game input was driven from them. Do not resume blind UI input loops.
