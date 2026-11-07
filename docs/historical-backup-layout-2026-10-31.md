> Historical private-backup documentation. Local-preservation statements are not current.

# Backup and restore

This is a private checkpoint of Open Amalur, created on 2026-10-31 without changing the existing Windows project, Android installation or game saves.

## Storage layout

The Git history contains source, build recipes, selected research/evidence, and continuation notes. Large generated outputs are stored as assets of the private `checkpoint-2026-10-31-v0.14.0` release:

- `open-amalur-windows-project-2026-10-31.zip`: Windows source, work directories, build artifacts, project-local extracted inputs and reference sources, except the exclusions below.
- `open-amalur-windows-evidence-2026-10-31.zip`: Windows output reports, native evidence, generated scene data, APKs and earlier packaged checkpoints outside the large script-corpus directories.
- `open-amalur-recovered-script-corpus-2026-10-31.zip`: The large recovered-script draft trees and existing initial-script draft archives.
- `open-amalur-mac-additions-2026-10-31.zip`: Mac-side files whose SHA-256 differs from the Windows file at the same path, or which have no Windows counterpart. These remain separate so neither version is overwritten.
- `windows-file-manifest.jsonl.gz`: Per-file Windows coverage, SHA-256 hashes of included files, archive assignment and explicit exclusion reasons.
- `mac-file-manifest.jsonl.gz`: Per-file Mac coverage, hashes, and whether Windows already contains identical bytes.
- `archive-manifest.json` and `SHA256SUMS`: Archive sizes and checksums.

The Git source view is intentionally smaller than the complete private checkpoint. A file missing from Git may still be fully preserved in a release archive; consult the manifests.

Git history was rewritten on 2026-10-31 to remove generated data. Each removed file was hash-checked inside the release archive listed here before the rewrite:

| Removed from Git | Release archive |
| --- | --- |
| `outputs/`, except notes and test inputs | `open-amalur-windows-evidence-2026-10-31.zip` |
| `src/scene-v*/`, `.log` and `.png` files under `work/`, and the three unlicensed reference folders | `open-amalur-windows-project-2026-10-31.zip` |
| `mac-coordination/` (paths in the archive omit this prefix) | `open-amalur-mac-additions-2026-10-31.zip` |

The manifests are unchanged, so their `git` fields describe the original checkpoint rather than current Git contents. `backup-metadata/SHA256SUMS` pins the release's copy of this document, so this edited copy will not match that entry; `verify_backup.py` checks the release copy.

## Exclusions retained locally

- Private signing keys and credential configuration.
- Native-game personal save/configuration backups in `native-state-before*` directories.
- Downloaded Android/Java/Ghidra toolchains, downloaded archives, Python package installations and Node dependencies. Node package manifests/lockfiles and existing toolchain reports are retained.
- Reinstallable caches and reference repository `.git` internals. Reference source files and revision/provenance metadata are preserved.
- The original game installation, which is outside the project root. No original `koa.exe` or full commercial `.pak` installation archive is included.

All original files remain untouched on their existing machines. These exclusions mean this backup is not a disk image or a backup of personal game saves. The private release includes project-local extracted research inputs and derived assets; keep the repository and release private.

## Restore procedure

1. Clone the private repository and download all release assets. Verify their SHA-256 values against `SHA256SUMS` and the manifests before extraction.
2. Extract the three Windows archives into the same **empty** project folder; their paths complement each other. Preserve relative paths. The historical default is `C:\Users\rwill\Documents\Opem Amalur`.
3. Extract Mac additions into a separate coordination folder. Consult their manifest before merging any same-path differences with the Windows project.
4. Read `work/CURRENT_STATE.txt`, `outputs/scene-v18/PROGRESS.txt` and `outputs/scene-v18/continuation.json`. Earlier top-level README files describe earlier stages.
5. Reinstall the recorded dependencies as needed: Python, Visual Studio Build Tools/CMake/Ninja, Android NDK r30 and the SDK build tools/platform used by the saved build scripts, JDK 21.0.13+9, Ghidra 12.1.4, and REA packages pinned by their lockfiles. Existing scripts contain machine-specific paths; review them before execution.
6. Restore the existing debug signing key separately if needed. Do not create a replacement key and install over the current tablet application expecting the signatures to match. The saved signed APK can be retained without rebuilding it.

Build directories are historical artifacts and may contain absolute paths; reconfigure them for a different machine. Do not execute native analysis workers, launch the original game, install APKs or touch saves solely to validate a restored backup.

## Integrity and operational policy

The backup records file hashes and verifies archive integrity and remote presence. It does not assert new engine correctness or full-game compatibility. Existing test reports are preserved as historical evidence; no engine tests or device operations were performed for this checkpoint.

Continue using Sol, keep builds/tests batched, preserve older checkpoints, and obtain approval before another Astra escalation. Engine work remains paused until the user resumes it.
