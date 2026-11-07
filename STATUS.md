# Final project status — November 6, 2026

Development is stopped at the owner's request. This document is an evidence summary, not a new validation run.

## Custom engine

The project produced a native GLES-based reconstruction with a Windows host and Android builds. Gorhart/shop, the woodland bridge and the opening room were investigated. Movement, collision, selected interactions, menus/inventory/save paths, character preview and creation boundaries received targeted tests. The latest packaged checkpoint recorded in this chat was Android v0.39.1/code 42; older top-level handoff sections were not fully consolidated.

This was an independently reconstructed runtime with authored policies as well as recovered contracts. It did not preserve all original engine behaviour. The original-image comparisons and targeted fixes did not establish game-wide placement, material, lighting, foliage, character or geometry correctness. Full tutorial/campaign completion was not verified. Character creation's acceptance checklist remains the definition of completion; staged Unicode/name input and patron-detail work must not be described as installed or fully vetted.

The owner preferred the reconstructed waterfalls to the original. That stylistic preference was recorded; waterfall appearance was deliberately not changed just to match the reference.

## Original engine and graphics layer

The analyzed koa.exe snapshot matches the installed Re-Reckoning build cs:15032:
`16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314`.

Fresh static audit: x86 PE32, 349 imports from 19 DLLs, 1,088-byte static TLS template and a three-entry SafeSEH table. This inventory is not a complete dynamic dependency or callback catalogue.

The project's own x86 D3D11-to-Vulkan layer and shader translator ran the actual game on Windows and under FEX/Proton on Android. Earlier records report 510 distinct recorded shaders passing SPIR-V validation; this is a bounded shader corpus, not all-game shader or pixel parity. Android texture issues and performance attribution were unresolved. The graphics bridge contains Windows/x86-specific code and is not an ARM library that only needs a different compiler flag.

## What the decompilation/recompilation work actually proved

- The retained Ghidra export had 45,957 pseudocode functions. That export did not compile as recovered engine source and is not published here.
- Five manually rewritten functions were used inside the original x86 process with limited original/replacement comparisons. The surrounding original executable still supplied the rest of the engine.
- The experimental translator emitted 73,971 entries, including unverified data-pointer seeds, and produced 50 ARM64 object chunks and a linked decoder harness. These counts are not engine completion percentages.
- The final audit found wrong function-entry execution, incorrect memory BT/BTS addressing, insufficient interprocedural flags, and further floating-point, atomic, TLS, exception and host-ABI gaps. A retained successful ARM execution/equivalence receipt for that generated decoder harness was not found. Compilation alone is not execution or equivalence.
- Separate manually recovered matrix and geometry kernels had useful original-x86/ARM comparisons. A captured real graphics workload also rendered on ARM. These do not establish an independently rebuilt original game loop.

See `docs/engine-rebuild-audit/` for precise source-level findings and qualifications.

## Why we stopped

Repeated scene-specific visual corrections did not produce reliable whole-game fidelity, and too much visual validation fell to the owner. The custom engine was explicitly stopped. The original-engine review identified a possible preservation route but did not produce a qualified whole-engine translator/runtime or a defensible completion date. The owner then ended active work and requested this public snapshot and local cleanup.

## Possible future work, without a commitment

A future maintainer could qualify an existing x86 lifting/runtime stack against the known failures, preserve the original engine's decisions, produce a standalone Windows rebuild, and address ARM/Android platform services and middleware. Full readable/matching source recovery and a first playable static recompilation are different milestones. Recent ports' fast release histories are useful precedents, not evidence that Amalur's missing runtime is solved.

No native full-game FPS prediction, compatibility percentage, completion date or continuing development commitment is made.
