# Shelved custom engine review — 2026-11-05

The owner stopped the original-engine native-port work and requested reconsideration of the shelved engine. This is a read-only review of the authoritative Windows source and saved results; no new tablet benchmark, build, install, or gameplay validation was performed. No original source, saves, keys, analysis databases, or build artifacts were changed.

## Recommendation

Make the custom ARM64 engine the primary development path for a native Android version we can build and change. Its demonstrated foundation is much stronger than the early scene viewer. Preserve the original-engine/Vulkan work as reference and keep the full native-original-engine port paused. This recommendation is about reaching useful native gameplay sooner; complete campaign compatibility and exact behavior remain unproven.

## What is actually there

Authoritative root: `C:\Users\rwill\Documents\Opem Amalur`. Custom runtime: `work/v19-host`; content tooling: `work/v20-char`, `work/v23-actors`, `work/v24-zones` and related earlier recovery folders. The manifest is version 0.33.0, versionCode 35, package `org.opemamalur.scene`. Numbered patch scripts such as patch_v062.py are patch sequence numbers, not app versions. The late Erathell test APK is a separate content build of this line.

Current source and saved records support: ARM64 GLES3 rendering; streamed outdoor terrain and collision; real meshes, textures and offline-baked animation clips; walking and shop/outdoor transitions; basic sword combat; limited inventory/equipment, loot, potions and save/load; local lighting, shadows, fog, sky, water and audio. Original Workbench Lua dispatch exists through an Android UI service.

Saved late v0.33 records describe a 10-minute tablet route run at 2520x1680 with water, real sounds and periodic player swings: frame interval p95 16.66 ms, worst frame 29.14 ms, GPU mean 7.91 ms, no frame over 40 ms, thermal status 0–1. That particular run had a sky bug. A later complete-terrain entry records p95 16.67 ms, worst 30 ms. These are historical project records inspected today, not freshly reproduced measurements or proof of full-game performance. Earlier overview-camera and broken-route results were explicitly retracted; do not reuse those results. Actor totals describe zone content; they do not mean all actors were fully simulated simultaneously.

## Why it advanced quickly, and the remaining risk

Progress combined recovered content with much simpler authored behavior. oa_actor_ai.h explicitly says the original behavior trees are not recovered. oa_items.h says powers, values and effects are authored. Combat and animation-selection rules contain host policies. The Lua bootstrap explicitly supplies no per-frame gameplay behavior. Workbench has a real recovered callback connected to an authored service, but crafting still lacks the original formula initialization. Animation baking still invokes a selected original x86 decompressor offline on Windows; the Android runtime is native.

The save structure contains location, position, facing/camera, health and the limited bag. It has no general quest state, dialogue state, progression or arbitrary persistent world-object state. Existing menus cover title, pause, options, HUD layout and inventory. This is a capable native gameplay prototype, not a demonstrated complete Amalur campaign runtime.

Other known gaps include terrain paint-map linkage, exact visual parity, original NPC schedules/behaviors, original navigation data, full item curves, abilities/progression, real dialogue/quests, comprehensive persistent world state and broad content compatibility. Some earlier source comments and packaging descriptions are stale; they must not override the actual code and later state entries.

## Next visible milestone

Resume from the preserved Dalentarth custom build, retaining the current installed app and signing key. Choose one short original quest near Gorhart and connect the minimum recovered content/services needed for the complete loop: NPC conversation, accepted objective, combat or collection, return/reward, and save/reload preserving the outcome. Keep the current rendering baseline while doing this. Record recovered behavior separately from deliberate host approximations; fail visibly on missing required services instead of reporting success through empty stubs.

This single end-to-end loop is a better decision test than another rendering or FPS checkpoint. It will expose whether the remaining script bindings, quest data and persistence can be extended systematically. Do not assume that every original function or every room needs to be reconstructed before this experiment.

## Evidence retained

Small private local snapshots of the Windows state, manifest and relevant source files are in `evidence/`, with SHA-256 values in `evidence-sha256.json`. The root README and some packaging purpose strings predate most of this functionality. The original route plan says the custom engine was frozen when the requested objective changed to using the original engine; the reviewed records do not show that it was abandoned because rendering performance had failed.
