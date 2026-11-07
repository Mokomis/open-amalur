# First integrated frame: depth coverage and caster winding

Static follow-up, 2026-11-05. Root's /private/tmp/oa-v44-first.png was viewed. Only capture, current source and CPU projection calculations were used. No renderer/UI/game operations and no shared source edits. New files only in this directory.

## Concrete depth mismatch

The inspected current work/v19-host/oa_post.c has `if(depth_only!=0)` returning before all VARIANT1 terrain coverage conditions. Therefore the depth prepass writes triangles that the corresponding color pass can discard:

- terrain_draw_set < -1;
- native terrain rows whose picked selector differs from terrain_draw_set;
- fallback proxies when native selector picked <5;
- disabled native terrain rows when use_native is false.

The prepass includes phases0..3 and runs the same streamed terrain draw lists. It must evaluate the exact same terrain selector/coverage predicate before returning. Otherwise an invisible terrain/proxy triangle can write depth, prevent real geometry behind it from drawing, and leave the clear/post-processed background visible. This is a concrete correctness bug; final attribution of the pictured holes still requires root's rebuild or depth probe.

The native sky module does not write depth. At the two reported pixels the actual captured sky triangles are at D3D/GL hardware depths .999984136 and .999981894 respectively. Ordinary rock/forest tens of thousands of units away is nearer. The sky cannot overwrite a nearer prepass depth or erase opaque color. Disabling native sky alone distinguishes sky color from clear color but does not identify the missing world coverage by itself.

Recommended focused depth probe at top-left pixels(650,300),(800,290): record hardware depth immediately after prepass and again after sky. They must be identical. Near depth plus background color implicates depth/color coverage disagreement; depth1 indicates missing scene prepass coverage. After color, identify the owning terrain row/picked selector if a near invisible occluder remains. A simple bypass of terrain depth prepass is a useful diagnostic, but the final fix is shared coverage logic.

Current android_scene.c restores sceneFBO, viewport, depthLEQUAL, depthMaskTRUE, blendOFF, cullOFF and colorMaskTRUE after AO/CSM. Root also added depthMaskTRUE immediately after native sky. The inspected sky code binds only its own VAO/textures/samplers, disables stencil, uses LEQUAL/no depth writes and no culling/blending. It unbinds its owned samplers afterward. Original native sky uses stencilEQUAL0 background; an equivalent filled scene depth is adequate for the current background-first ordering, provided depth and color coverage match.

## Caster culling correction

My original module's glFrontFace(GL_CCW) was an unsupported assumption and should be corrected to GL_CW under root's unchanged nativeXY projection convention. Original active caster phases99/101/103 ALL declare VK_FRONT_FACE_CLOCKWISE. The dominant ordinary caster pipelines8927/12371 cullBACK. Leaf pipeline12373 and two far-only12378 draws cullNONE. Two far-only12370 draws cullFRONT. Full per-phase counts are in caster-orientation-validation.json.

Captured viewport is(x0,y1024,width1024,height−1024). This is recorded explicitly; pipeline naming alone was not used as the geometric check. The emitted GL adapter changes Z only, preserving original clipXY. Captured far CSM maps an upward, worldXY CCW triangle [(0,0,0),(100,0,0),(0,100,0)] to signed NDC area−.000120606966, i.e. GL CW. The native light right/up basis points its cross product opposite the sun; changing only projection Z does not change winding. The previously delivered portable matrix comparison reproduces those native matrices to about1e−6.

The actual first native caster draw69945 has948 triangles:399 CW and549 CCW under the captured matrix. These are ordinary object faces, so both orientations are expected. Vertex/index buffers, dynamic matrix and first12 signed areas are retained. Culling the opposite winding changes which object faces cast; no blanket claim that all mesh triangles have one orientation is made.

The module should begin with frontFaceCW/backCull. Root's oa_stream_draw_world_range currently disables culling for phase3 or materialFamily6 and never re-enables it for the next ordinary draw. Therefore exact per-material caster culling needs restoring the appropriate state on each material/draw, rather than relying only on begin(). Main scene culling remains root's separate policy. Shadow resolve only blends the G shadow channel of AOshadow, so caster winding changes cannot directly erase world geometry or create sky-colored holes.

## Evidence

analyse_sky_depth.py and sky-pixel-depths.json use the original procedural/captured sky mesh and full native sky VP. validate_caster_orientation.py and caster-orientation-validation.json retain raster states and project both a known upward face and original caster triangles. first-caster.json plus buffer12236/12238 preserve active material matrix and geometry. All calculations are CPU-only; root owns GPU verification.
