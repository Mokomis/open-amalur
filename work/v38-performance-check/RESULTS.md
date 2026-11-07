# Android native performance feasibility check

November 5, 2026. Existing builds only; no compilation, installation, driver changes, or clock/thermal overrides.

## Decision and educated guess

A stable **30 FPS is a plausible first target** on the attached OPPO tablet. For a reasonably optimized native port at **1536 × 864**, use these planning scenarios:

| Scenario | Estimated full-game FPS |
|---|---:|
| Normal representative play | 30–45 |
| Heavier scenes or thermal throttling | 20–30 |
| Light scenes with successful backend optimization | 45–60 |

These are engineering estimates, not observed native gameplay, statistical confidence intervals, or guaranteed minimums. Unexamined worst cases could fall below 20 FPS. The evidence supports a further substantive native subsystem milestone; it does not justify committing to a full engine reconstruction on an assumed 60 FPS outcome. The scope of engine recovery remains a major separate risk.

## Fresh measurements

The existing ARM64 app replayed the real woodland-bridge graphics workload without FEX, Wine, or DroidDeck. It used the stock Android Adreno Vulkan driver. This is a fixed recorded frame, with no game simulation, live animation, collision, or streaming.

- Resolution: **1536 × 864**.
- 900 redraws: 150 warm-up, **750 timed frames**, offscreen, with no screenshots during timing.
- Average: **31.14 FPS / 32.1 ms per frame**.
- Median: 32.23 ms; 95th percentile: 39.36 ms.
- Timed duration: 24.08 seconds. Process CPU: **19.95 ms per frame**.
- Eight-second CPU-cycle profile, 440 samples: **44.76% Vulkan driver, 31.99% replay library, 19.75% libc**, approximately 3.5% other.
- Almost all sampled CPU work ran on one rendering thread. The `getenv` function alone accounted for 9.24% of sampled cycles, illustrating remaining framework overhead.

CPU-cycle percentages are not percentages of wall time. No GPU timestamp timing was collected. The gap between process CPU time and frame duration cannot be assigned entirely to GPU work. This short run is not sustained thermal testing. Earlier comparable fixed-frame runs measured 30.0 and 30.9 FPS.

The original Windows game was already at the matching woodland bridge. An eight-second sample found approximately **88% of process CPU time in the main and rendering threads**. Unpausing was requested, but not verified during the sample; the final screenshot showed Game Paused. This is a stationary rendering sample, not confirmed gameplay, movement, or combat.

## How the estimate was formed

The measured 32.1 ms frame is the anchor. A native engine would remove capture decoding and replay bookkeeping, but add game updates and dynamic resource work. The CPU profile shows substantial framework work remains; it does not establish exactly how much wall time a direct renderer would recover.

For budget intuition only, removing roughly **6–12 ms** of replay-related cost and adding roughly **4–10 ms** of game work produces approximately **24–36 ms** frames, or about **28–42 FPS**. Both budgets are unmeasured assumptions, and their overlap is unknown. They support a planning range around 30–45 FPS with some backend optimization, rather than a promise. The heavier and optimistic scenarios are additional judgments, not separately tested scenes.

Earlier FEX gameplay readings ranged from 25.6 to 55 FPS under different scene and thermal conditions. They are context, not a matched comparison. **No FEX-overhead percentage has been established.** Stock Android Vulkan and DroidDeck's Turnip driver also differ.

## Threading and useful changes

The original job-manager setup at **0x00b05f10** creates four workers. Separate main/rendering threads and parallel/sequential Bullet scheduler code also exist. The active physics scheduler was not established.

Worker counts, job partitioning, and synchronization can be changed in recovered engine code. More workers alone are unlikely to solve the observed concentration of main/render work. The useful priorities are efficient Vulkan submission/state/buffer handling and removal of replay work; parallel jobs should be expanded where genuinely independent work exists. No global Android affinity or thermal changes were made.

## Bounded FEX attempt

DroidDeck and Steam opened successfully. Two input methods did not advance the selected Steam game tile, so this attempt stopped without another UI investigation. There is **no fresh FEX gameplay profile**. Steam was left open on the tablet; the Windows game remained at the bridge with pause visible. No save was loaded or intentionally written, and original app data and signing keys were not replaced.

## Saved evidence

`summary.json`, `native-900/measurements.json`, `native-900/replay.log`, native CPU profiles and raw cycle data, Windows thread timings/logs, and screenshots are retained beside this report. Windows copy: `C:\Users\rwill\Documents\Opem Amalur\work\v38-performance-check`. All evidence remains private and local.
