# Recent recompilation timeline review — November 6, 2026

Dated public milestones were checked against GitHub commit timestamps and release API assets. They are not independently measured developer hours or comprehensive gameplay certification.

| Project | Start evidence | Published milestone | Elapsed |
| --- | --- | --- | --- |
| Lost Odyssey Recomp | Initial skeleton, 2026-09-03T23:28:09Z, commit 6b162ddbd57c97978cfde5fba29745b959ecb353 | v1.0.0, 2026-10-17T07:19:07Z; Windows/Linux/macOS ARM64/Android packages | 43.327 days |
| Ninja Gaiden Black | New-game template, 2026-10-05T15:10:09Z, commit 0f7aa77e1ec2ed67420459bb93288aae467bf178 | Desktop beta October 15; Android v0.9.45, 2026-10-30T16:04:49Z | 10.012 / 25.038 days |
| Skies of Arcadia Legends | First retained commit, 2026-10-12T21:04:51Z, f3fd5a6a0affda2bec2c33881decdcd6e84840e2 | Android/desktop v0.9.1-beta, 2026-10-17T14:32:26Z | 4.727 days of retained history; not proof of total development time |

These projects reuse substantial translation, emulator/runtime and graphics infrastructure. The relevant x86 precedent is Ninja Gaiden Black's use of xboxrecomp and existing graphics/audio work. Xbox XBE runtime services differ from a Windows PE32/D3D11 game's services; no Amalur compatibility is established by this comparison.

A prior blanket year-or-years estimate was withdrawn as an unsupported baseline for a first playable static recompilation. Full matching/readable source reconstruction and a first playable port are different milestones. No qualified Amalur runtime or measured recovery rate was established before the owner stopped the project, so there is no validated completion date.

Sources:
- https://github.com/freefrank/LostOdysseyRecomp/commit/6b162ddbd57c97978cfde5fba29745b959ecb353
- https://github.com/freefrank/LostOdysseyRecomp/releases/tag/v1.0.0
- https://github.com/gamboozino/ngbrecomp/commit/0f7aa77e1ec2ed67420459bb93288aae467bf178
- https://github.com/gamboozino/ngbrecomp/releases/tag/v0.9.45
- https://github.com/gamboozino/ngbrecomp/blob/master/THIRD_PARTY.md
- https://github.com/ogdanimal/SkiesOfArcadiaLegends-Recomp/commit/f3fd5a6a0affda2bec2c33881decdcd6e84840e2
- https://github.com/ogdanimal/SkiesOfArcadiaLegends-Recomp/releases/tag/v0.9.1-beta
- https://github.com/sp00nznet/xboxrecomp
