# Native FX integration review

No actionable introduced memory, VAO-layout, framebuffer-feedback or API bug found in the reviewed diff. The receipt records exact reviewed source/baseline hashes and checks. Review covered `oa_fx.c`, `oa_fx.h` and the `android_scene.c` call/snapshot integration against `before-native-fx`.

The20float/80-byte instance allocation, write stride, attribute offsets and per-instance divisors agree. All20slots are initialized. Particle place indices are initialized at spawn and preserved by swap-delete. The new metadata rows and optional authored texture chains are validated before their payloads are copied/uploaded. The endpoint lookup fix removes the prior out-of-range key access; unsigned RNG wrap is defined.

The soft-depth sampler reads the separate opaque snapshot, not the currently attached scene depth. Both snapshot paths restore the scene framebuffer; depth-ready gates binding. Sampling uses GL-bottom-left coordinates consistently. Native clipZ, highp inverse depth, unusual soft-zero branch, alpha fog transmission and additive blend state agree with the existing neutral-tint PS1042 contract. Native-only shape behavior stays behind its flags; the explicit live shape toggle resets simulation as requested.

This is static source review only. No source edits, builds, original game launch or replay occurred. Runtime shader/link status, actual packaged optional files and Windows/Android image behavior remain parent validation. The inferred producer input/sign choice is a documented fidelity limit rather than a claimed memory/GL implementation defect. Original asset parser/allocation hardening was not expanded into this bounded diff review.
