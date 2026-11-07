# Open Amalur

**Development stopped on November 6, 2026.** This is a public source and research snapshot, not a finished game or a complete native port of Kingdoms of Amalur: Re-Reckoning.

Open Amalur investigated two approaches: a custom native engine that reads recovered game data, and preservation of the original engine through graphics translation, reverse engineering and experimental recompilation. Both are stopped. No further development or release date is promised.

## Why development stopped

The custom engine made rapid progress on selected scenes, but did not establish reliable game-wide visual or behavioural fidelity. Missing or extra objects and foliage, material/texture discrepancies, flashing surfaces, incomplete geometry and character issues required repeated investigation. Improvements to shared systems did not demonstrate that these problems were resolved across the game, and the owner was having to identify too many of them manually. The owner stopped this approach and subsequently requested publication and removal of local project files.

The original-engine route remains incomplete. Exported pseudocode and compiled translated functions were not a working rebuilt engine. A subsequent audit found concrete defects in the experimental translator. Neither the available evidence nor other projects' release schedules establishes an Amalur completion date.

## What worked, and the limits

| Area | Demonstrated progress | Important limit |
| --- | --- | --- |
| Custom native runtime | Selected real game scenes rendered on Windows and Android; walking, collision, streaming and selected interactions were exercised. | A partial reconstruction; no full campaign or game-wide parity. |
| Rendering | Terrain, materials, lighting, shadows, water, foliage and post-processing implementations; matched-view comparisons and selected original-code contracts. | Approximate or incomplete paths remain. A good view is not proof for other scenes. |
| Canopy | Corrected/Dense options, with the previous denser coverage retained; tested in the selected scene. | Not proof of all native visibility/LOD behaviour. |
| UI and character creation | New UI, expanded character preview and appearance pipeline, draft persistence and selected game-start/reload tests. Last packaged custom Android checkpoint: v0.39.1, version code 42. | The complete acceptance gate and every original option were not independently established. Unicode/patron presentation work includes staged changes that were not deployed. |
| Asset/script research | Extractors, format parsers, Lua/runtime/binding work, native property and placement investigations, build recipes and tests. | Recovered content and partial contracts do not constitute the complete engine. |
| Original engine + Vulkan | Historical Windows runs of the real game through the project's D3D11-to-Vulkan layer, and Android runs through FEX/Proton. | Android CPU cost and texture problems remained unresolved; this was not native ARM engine execution. |
| Native ARM experiments | A real captured frame replayed natively; bounded recovered kernels and geometry paths compared against original outputs. | Captured-scene replay excludes live game simulation, animation and streaming. Its frame rate is not native full-game FPS. |
| Engine recompilation | Analysis, five manually rewritten functions used within the original process, and an experimental x86-to-C translator with ARM64 compilation artifacts. | No standalone rebuilt engine. The translator has known correctness defects and lacks complete runtime/platform integration. |

See [STATUS.md](STATUS.md) for the final evidence boundaries and [ARCHIVE_CONTENTS.md](ARCHIVE_CONTENTS.md) for what is included.

## Source map

- `work/v19-host/`: shared custom engine and Android runtime source.
- `work/v40-windows-host/`: Windows host, controls and preparation scripts.
- `work/v43-scene-fidelity/` through `work/v50-character-complete/`: later fidelity, canopy, performance, opening-room and character work, including unfinished stages.
- `work/v30-engine/`: original-engine graphics layer, shader translator, recording/replacement proxy, analysis scripts and experimental recompilation tools.
- `work/v31-native-slice/` through `work/v38-performance-check/`: bounded native experiments and capture/replay work.
- `src/`, `tests/`, earlier `work/`: parsers, reconstruction/runtime experiments and tests.
- `coordination/`: separate Mac-side scripts and notes; they do not overwrite Windows counterparts.
- `docs/engine-rebuild-audit/`: source-level translator/platform findings from the final review.
- `tools/local-worker/`: historical local Qwen/REA worker source and setup notes. Machine paths and target registrations are examples from the old installation.

## Building and game data

This repository contains no original game executable, installed game archives, extracted game media, recovered Lua corpus, recordings, APKs, saves or signing keys. You need your own game data and must regenerate or supply the private inputs expected by the relevant recipe. **A clone alone is not a complete APK build environment.**

Build and operator notes are historical, often contain machine-specific paths, and are not a promise of a one-command clean build. No engine builds or device tests were run merely to publish this snapshot. Existing validation reports describe the particular source, inputs and hosts recorded in those reports.

Earlier notes may say “active”, “complete” or describe a different installed version. This README and STATUS.md override those continuation instructions. Third-party code retains its own notices; a repository name or inclusion does not grant rights to commercial game data.
