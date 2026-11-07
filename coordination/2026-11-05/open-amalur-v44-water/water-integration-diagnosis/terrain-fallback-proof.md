# Terrain hole proof

After native-water front-face correction, `/private/tmp/oa-v44-waterfixed.png` confirms a dark, reflective river and persistent pale background gaps.

Using the exact captured reference view-projection and original `work/v22-stress/zone-dal/zone_pos.npy` geometry, ray through pixel (650,300) first intersects ground triangle 7228188, legacy material253, at (-11078.749177,-69567.314993,7606.847622). Its original source cell is (-2,-11). The shipped terrain selector at tile(1826,657) is82, selecting native terrain set2. All three original cell LODs have zero native-terrain draw records.

At pixel(650,230), triangle7240966 intersects at (-12253.093443,-68549.886100,9556.720998), also source cell(-2,-11). Selector tile(1803,677) is82 and selects set2. Behind both, ground in cell(-3,-11) selects set0; that cell also contains no replacement terrain at any LOD.

The active shader therefore discards these exact visible legacy triangles because `terrain_supported_sets` is global. The earlier depth pass already accepted the triangles before reaching selector discard, preserving depth while leaving clear color. Correcting native-water winding cannot repair these background gaps.

Fix: set `terrain_supported_sets` per current cell/LOD draw list, using only actual native terrain sets present in that q. Set zero for unsupported cell/LOD lists. Existing shader fallback then preserves original ground whenever no replacement exists.

Complete numeric evidence is Windows `work/v44-native-fidelity/water-research/water-integration-diagnosis/terrain-hole-ground-rays.json`. No original assets or renderer sources were modified by this investigation.
