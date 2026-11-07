# First integrated water frame: concrete facing defect

The active native water module calls glFrontFace(GL_CCW) with backface culling enabled. This removes the visible river/pond surfaces under the actual native reference VP. Homogeneous clipping and signed projected triangle areas were computed from the original recorded VP and the exact recovered meshes:

| Draw | Visible clipped CW triangles | CCW triangles |
| --- | ---: | ---: |
|72952|32|0|
|72957|281|0|
|72962|21|0|
|72967|40|20|
|72972|26|0|
|72974|34|0|

Native captured pipeline state also declares CLOCKWISE front faces. Earlier CCW guidance based on world triangle normals missed the native VP orientation; this diagnosis supersedes that guidance. Root owns the actual source change.

For the reference frame, CW restores the horizontal surfaces. A production fix must also support normal Android camera_matrix(), whose standard RH view/projection has the opposite facing sign. Use the caller's perspective VP:

    h=dot(cross(VP.row0.xyz,VP.row1.xyz),VP.row3.xyz)
    glFrontFace(h>0 ? GL_CW : GL_CCW)

`water_front_face.h` is the ready helper. Native reference h=+3.055998411; the normal camera's source construction gives h<0. D3D-to-GL z remapping affects neither row0,row1 nor row3. Hardcoding CW globally would fix the reference and then cull normal-camera surfaces incorrectly.

Alpha/depth equations were checked and do not support a change: root's inverse-depth recovery agrees with native bound values within approximately2ppm. Saving original D3D clip.z as.5*(GLclip.z+clip.w) matches the native VS's complete clip varying. Hardware depth is0..1. Native top-left screen UV plus final GL sampling flip correctly selects the lower-left snapshot. Per-vertex scale/world positions remain the recorded native transforms; no world-Z offset was invented.

`projected-water-coverage.json` records exact homogeneous-clipped coverage for selected pixels. Pond72974 covers the dry-bed probes(500,600),(700,700),(1000,550), with CW facing. Thus culling explains the missing water there.

The approximate white-hole point(650,300) is outside every recovered native water triangle after full clipping. A second bounded source check also finds no remaining legacy river triangle there. Water output cannot explain that specific pixel under this VP. At(900,430), native pond72952 projects, and one remaining legacy riverwaterfall triangle from cell(-2,-13) lies behind it. Root's sky/depth-state fix and a new integrated frame will establish which white regions disappear; no result of that future frame is claimed here.

Only new diagnosis files were written. Existing source, prepared assets, camera state and application/UI were untouched.
