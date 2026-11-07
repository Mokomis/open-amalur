# Integrated frame diagnosis: terrain fallback

Evidence frame: `/private/tmp/oa-v44-waterfixed.png` (1536x864). Corrected native-water culling restores the dark reflective river. Large pale gaps in background slopes remain.

The active staged `oa_stream.c:211` supplies `terrain_supported_sets` once per phase from the global `s->terrain_sets`. There is no per-cell override in the cell/draw loop (214–217). Native terrain replacement draws are scoped to the reference cells.

In `oa_post.c:47–53`, a selector value below five is accepted if its bit exists in that global mask; a legacy ground draw (`terrain_draw_set==-1`) then discards the pixel. No matching native paint triangle is required to exist in the current cell or LOD. Meanwhile `depth_only` returns before this logic at line29, so depth may already be present where the color pass later discards. Scene clear color remains visible.

Concrete correction: before each phase1 cell draw, derive the supported-set mask from native terrain draw records actually present in the current `q`. Supply that mask to `terrain_supported_sets`, including zero for cells without replacement triangles. Keep the selector and exact native materials unchanged. If a set is not present, existing shader logic resets picked=7 and retains legacy terrain. This also makes fallback work for LODs that have no appended native paint geometry.

Water-specific exclusions: homogeneous clipping of all eight native water meshes gives no triangle coverage at pixel (650,300). Retained legacy water/fall triangles also give no coverage there. Thus this location cannot be a water shader output under the captured reference VP.

The original water depth linearization, screen-coordinate adaptation, D3D clip-z varying and alpha equation were independently checked against captured native shader contracts and require no correction for this issue.
