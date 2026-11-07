# Leaf range integration review

No actionable introduced memory, state, culling, shadow-path or API bug found in the focused source review. Exact reviewed source and baseline hashes are in review-receipt.json.

The existing OARGEO1 parser and dynamic row accessor already work independently of slot. Removing the region-only condition applies validated range checks to TREE_LEAF without changing buffer layout/lifetime. The same world_range path handles native main depth, lit color and shadow cascades; all use maincamera last_eye for the authored distance decision.

Stats field layout/getter/logging agree. Expanded desktop material/depth probe arrays, loops, GLSLuniform array, temporary texture/viewport dimensions and readback sizes are consistent:6 material points,12depth points. No new framebuffer feedback or state restoration problem found.

This is static source review only. No source edits, builds or replay occurred. Parent owns staged asset validation and Windows/Android runtime checks. Rejection stats count visits across passes, rather than unique source objects.
