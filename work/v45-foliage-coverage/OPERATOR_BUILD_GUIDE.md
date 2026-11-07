# Windows build and deployment operations

The live project is C:\Users\rwill\Documents\Opem Amalur, outside Git. Keep any Git clone separate. Read canonical AGENTS.md first. Preserve the current key and databases. The existing custom-engine preview is currently closed; scheduled task OA_CustomEngine_Windows_v40 launches the normal town view.

## One build after a batch of source edits

Windows PowerShell, from the project directory:

```powershell
& 'C:\Users\rwill\AppData\Local\Programs\Python\Python312\python.exe' .\work\v45-foliage-coverage\build_renderer_batch.py
```

This reuses existing Visual Studio/CMake/Ninja/NDK installations, builds Windows and ARM64, preserves the previous executable/library/receipt in build-receipts, and writes the source/binary hashes required by packaging. It refuses to interrupt an open preview. Source-input changes during compilation invalidate the receipt. Logs are retained per batch. The helper was syntax-checked; its underlying build commands were already exercised successfully for R3, so no extra build was run merely to retest the helper.

The direct Windows build remains work\v40-windows-host\build.cmd. ARM target is work\v19-host\build-android-arm64, target opem_amalur_scene. Data-only adjustments can reuse a verified binary; rebuild when source changes warrant it.

The R3 package recipe is work\v45-foliage-coverage\package_android_v036_r3.py. It is intentionally one-shot and refuses to overwrite its existing APK. For the next revision, create a separate staging/output name, preserve Android texture payloads t0..679, and retain uncompressed resources.arsc plus alignment/signature checks. It verifies the source receipt before packaging. Its auto asset scan includes optional Region/leaf/shadow/FX data. Reuse the existing signing key on Windows; never copy it.

One-time integration/staging scripts preserve historical input hashes and are not the normal build entry point. Actual source, build receipt and saved review fixes are authoritative; do not rerun an old integration script over the live working folder.

## Tablet connected to the Mac: optional direct Windows installation

To avoid copying another 1GB APK onto a nearly full Mac disk, a temporary localhost-only SSH tunnel was validated:

```sh
ssh -M -S /private/tmp/oa-v45-adb-control.sock -fNT -o ExitOnForwardFailure=yes -R 127.0.0.1:15037:127.0.0.1:5037 open-rune-windows
```

Then on Windows:

```powershell
$adb = 'C:\Users\rwill\Documents\Opem Amalur\tools\android\sdk\platform-tools\adb.exe'
& $adb -H 127.0.0.1 -P 15037 devices
& $adb -H 127.0.0.1 -P 15037 -s 99cc517a install -r 'C:\Users\rwill\Documents\Opem Amalur\outputs\scene-v45-r3\open-amalur-v0.36-r3-arm64.apk'
```

Check that port15037 and the chosen control socket are free before starting a new tunnel; use a different private port/socket if another thread owns them. The Mac ADB server must already see the unlocked tablet. Both tunnel endpoints bind localhost. Do not uninstall the app or replace its signing key. Verify the installed APK hash and actual new-feature draw logs.

Close only this task's tunnel on the Mac:

```sh
ssh -S /private/tmp/oa-v45-adb-control.sock -O exit open-rune-windows
```

That tunnel is now closed. Mac ADB remains running. Temporary profile/position/heading/resolution settings and USB stay-awake were restored; the original save/settings hashes are unchanged.

## Evidence and recovery

FINAL_VISUAL_REVIEW.md and android-validation-final.json record actual scope and remaining visibility/LOD limits. outputs\scene-v45-r3 contains the signed APK, immutable source-build receipt and private incremental restore kit. The restore kit requires the preserved R4 baseline/dependencies; it is not a standalone game distribution. Never upload game data, decompiler databases, APKs or the signing key to GitHub.

When appending materials, update the matching material-count headers in leaf-index.bin (u32 at16), region-index.bin (u32 at12) and shadow-index.bin (u32 at12), together with material/native-profile counts. Update index.bin texture count at12 as needed. Keep intentional zero-triangle Region metadata rows; they expand bounds and have no r-cell file.
