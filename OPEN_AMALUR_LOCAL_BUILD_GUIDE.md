# Open Amalur local build and tool access guide

Open Amalur's complete working environment is on **ROBMACHINEX**, under the Windows account **rwill**. The local project contains the source, generated inputs, build outputs and installed tools needed for the current Android build. A cleaned GitHub clone contains only part of that environment.

Paths and tool versions below were checked on Windows on **2026-10-31**. Engine development remains paused. Access checks in this guide inspect files and version information; building, packaging, native analysis and device installation are separate operations.

## Connecting Claude to the working machine

Claude needs a local terminal or an explicitly configured connection to Windows. Access to the GitHub repository alone does not expose the Windows filesystem, installed tools or tablet. A cloud coding container also needs an actual route and authentication to this private LAN machine.

| Item | Value |
| --- | --- |
| Windows computer name | `ROBMACHINEX` |
| Windows account | `rwill` |
| LAN address at verification | `192.168.68.52` |
| SSH port | `22` |
| Existing SSH alias on the Mac | `open-rune-windows` |
| Complete Windows project | `C:\Users\rwill\Documents\Opem Amalur` |
| Mac project and coordination files | `/Users/rwillmore/Documents/Codex/2026-10-29/new-project-project-name-is-opem` |

The project name is **Open Amalur**. Keep the existing Windows directory spelling `Opem Amalur`: many scripts deliberately use that exact path.

If Claude runs on the same Mac account with terminal and LAN permissions, first try:

```sh
ssh -o BatchMode=yes -o ConnectTimeout=8 open-rune-windows hostname
```

Expected output: `ROBMACHINEX`. The existing SSH alias uses the Mac's local SSH configuration and existing authentication. Do not copy private keys into chat or a repository. An alias in one user's SSH configuration is not automatically available to another account or a cloud container.

The Mac project also has `work/windows_probe.py`. It reads PowerShell from standard input and runs it through this SSH alias using an encoded command, which handles Windows paths and quoting:

```sh
cd '/Users/rwillmore/Documents/Codex/2026-10-29/new-project-project-name-is-opem'
python3 work/windows_probe.py <<'PS'
$ProgressPreference = 'SilentlyContinue'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
python 'C:\Users\rwill\Documents\Opem Amalur\work\claude_access_probe.py'
PS
```

If Claude runs directly on Windows, open a PowerShell terminal and use:

```powershell
Set-Location 'C:\Users\rwill\Documents\Opem Amalur'
python work\claude_access_probe.py
```

The probe prints JSON with path checks, tool versions, package metadata and the saved APK hash. It does not build, install, start an ADB server, launch the game, start REA or read private key contents. A successful probe exits with code `0` and reports no `missing_paths`. The checked environment passed on 2026-10-31.

## Which copy contains what

| Location | Contents and intended use |
| --- | --- |
| Windows `C:\Users\rwill\Documents\Opem Amalur` | Authoritative complete working folder. Includes `outputs/`, extracted inputs, toolchains and build artifacts. It is currently **not a Git checkout**. |
| `https://github.com/Mokomis/open-amalur` | Private, cleaned source repository. After the history rewrite it contains 2,357 tracked files. A clone alone cannot build the APK. |
| GitHub release `checkpoint-2026-10-31-v0.14.0` | Full checkpoint archives, including generated data, recovered scripts, evidence and APKs. Restore these when setting up another machine. |
| Windows `C:\Users\rwill\Documents\Open Amalur Backups\2026-10-31` | Locally retained checkpoint ZIPs, manifests and the original source staging export. |
| Mac `backup/github-2026-10-31/repository` | Fresh clone of the cleaned GitHub history. Its full path is relative to the Mac project above. |
| Mac `backup/github-2026-10-31/repository-pre-rewrite-retired` | Historical staging copy. Its Git metadata is renamed `.git-retired`; leave it retired. |

Keep new Git clones separate from the complete Windows working folder. Follow the current repository's `BACKUP_AND_RESTORE.md` when restoring. The old manifest `git` fields describe the original checkpoint selection, not the cleaned repository's current contents.

## Windows project files

All paths in this section are relative to `C:\Users\rwill\Documents\Opem Amalur`.

| Path | Purpose |
| --- | --- |
| `work\CURRENT_STATE.txt` | Cumulative project handoff. Read the latest V18 section first. |
| `outputs\scene-v18\PROGRESS.txt` and `continuation.json` | Latest completed lighting/build/device checkpoint and unresolved questions. |
| `src\amalur_script.py` | Havok Script structural parser and bytecode disassembly. |
| `src\amalur_reconstruct.py`, `src\cache_flow.py` | Lua reconstruction and supporting analysis. |
| `src\runtime\` | Recovered-script compatibility helpers and engine bindings. |
| `tests\` | Python parser/reconstruction tests; some require the original local fixtures. |
| `work\v18-host\` | Current Android host, renderer, lighting, input and interaction sources. |
| `work\v18-host\CMakeLists.txt` and `android_scene.cmake` | Current CMake build definition and Android shared-library sources. |
| `work\v18-host\build_validate.cmd` | Batched Windows input-test build and Android library build. |
| `work\v18-host\package_android.py` | Assemble, align, sign and verify the current APK. |
| `work\v18-host\verify_android_package_inputs.py` | Package coherence checks; writes a validation receipt. |
| `work\v08-portable\` | C Lua embedding/runtime used by later builds, including vendored Lua 5.1.5. |
| `work\v08-portable\runtime\` | Lua runtime support files packaged into the APK. |
| `work\v08-scripts\`, `work\v08-scene\` | Scene/bootstrap support, recovered-module adaptation and package-readiness logic. |
| `work\v09-collision\` | Collision support, fixture tests and scene walking checks. |
| `work\v09-textures\` | Texture decoding, material sidecar format and GLES material renderer. |
| `work\v15-properties\` | Confirmed compiled native type decoder and real Workbench record work. |
| `work\v16-host\`, `work\v16-alchemy\` | Interaction/inventory services and alchemy data integration. |
| `work\v17-host\`, `work\v17-props\` | Workbench visual placement, native matrix evidence and geometry generation. |
| `work\v18-lighting\` | Light extraction/export helpers and the historical native-analysis worker. |
| `work\scene-inputs-v07\`, `work\scene-inputs-v09\`, `work\v17-inputs\`, `work\v18-inputs\` | Original extracted inputs used by the documented processing stages. |
| `outputs\` | Required generated scene/script data, evidence, validation logs and packaged checkpoints. Keep this directory. |

Version directory names identify historical work stages; they do not all equal the Android app version. The current app is **v0.14.0**, built from **v18-host**, and still depends on earlier stages. The old Windows root README describes an earlier parser milestone; use the current GitHub README plus the latest continuation notes for the overall state.

## Installed system tools

| Tool | Verified version | Executable or environment |
| --- | --- | --- |
| Python | 3.12.10 | `C:\Users\rwill\AppData\Local\Programs\Python\Python312\python.exe` |
| Node.js | 26.13.0 | `C:\Program Files\nodejs\node.exe` |
| npm | Installed alongside Node | `C:\Program Files\nodejs\npm.cmd`; `npm.ps1` also exists |
| Git for Windows | 2.56.0.windows.3 | `C:\Program Files\Git\cmd\git.exe` |
| CMake | 4.4.4 | `C:\Program Files\CMake\bin\cmake.exe` |
| Visual Studio Build Tools 2026 | 18.11.12324.101 | `C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools` |
| MSVC toolset | 14.51.36231 directory | `VC\Tools\MSVC\14.51.36231\bin\Hostx64\x64\cl.exe` under the Visual Studio directory |
| Ninja | 1.13.2 | `Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe` under the Visual Studio directory |
| OpenSSH and tar | Windows-provided | `C:\Windows\System32\OpenSSH\ssh.exe`, `C:\Windows\System32\tar.exe` |

The developer-shell setup files are `VC\Auxiliary\Build\vcvars64.bat` and `vcvars32.bat` under the Visual Studio directory. The current Android build script initializes the x64 environment. The historical native matrix probe uses the x86 environment because the original game executable is 32-bit.

Python, Node, Git and CMake resolve in the checked SSH session. Ninja, Java, ADB and the compiler are not all on that session's normal PATH; use the explicit paths or the existing build scripts.

## Installed project tools

Paths below are relative to the Windows project root.

| Tool | Verified version | Location |
| --- | --- | --- |
| Android NDK | r30, 30.0.16248370 | `tools\android\android-ndk-r30` |
| Android Clang | 21.0.0 | `tools\android\android-ndk-r30\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe` |
| LLVM inspection tools | Bundled with NDK | Same `bin` directory; includes `llvm-readelf.exe` |
| Android SDK platform | API 35, revision 2 | `tools\android\sdk\android-35\android.jar` |
| Android build tools | 35.0.0 | `tools\android\sdk\android-15\` contains `aapt2.exe`, `zipalign.exe`, `lib\apksigner.jar` |
| Android platform tools | 37.0.1-15733141 | `tools\android\sdk\platform-tools\adb.exe` reports ADB 1.0.41 |
| Temurin OpenJDK | 21.0.13+9 | `tools\jdk-21.0.13+9\bin\java.exe`; includes `keytool.exe` |
| Ghidra | 12.1.4 PUBLIC | `tools\ghidra_12.1.4_PUBLIC` |
| REA | 6.8.0 installed | `tools\rea\node_modules\rea-agents\scripts\rea.mjs` |
| Frida Node package | 17.23.2 | `tools\rea-frida\node_modules\frida` |
| luaparse | 0.3.1 installed | `tools\lua-validation\node_modules\luaparse` |
| Lua C source | Exactly 5.1.5 | `work\v08-portable\third_party\lua-5.1.5` |
| Capstone Python package | 5.0.9 | `tools\python-libs\capstone` |
| Lupa Python package | 2.6 | `tools\python-libs\lupa` |
| pypdf Python package | 6.21.4 | `tools\python-libs\pypdf`; an available utility rather than an APK build requirement |

The SDK directory called `android-15` contains **build tools 35.0.0**; do not infer its version from the directory name or rename it. API 35's platform JAR is in the separate `android-35` directory.

The three direct Node tool environments retain their `package.json` and `package-lock.json` under `tools\rea`, `tools\rea-frida` and `tools\lua-validation`. The table identifies the versions actually installed, including where a package declaration allows a range.

Some Python helpers add `tools\python-libs` to `sys.path`. For a new Python terminal that needs these local packages, set the path for that process:

```powershell
$env:PYTHONPATH = 'C:\Users\rwill\Documents\Opem Amalur\tools\python-libs'
```

The engine CMake files require the vendored Lua 5.1.5 source. Lupa is a separate analysis/validation dependency.

`tools\downloads` retains the NDK, SDK platform/build/platform-tools, JDK, Ghidra and Lua download archives, Android repository metadata, and `Kingdoms-of-Amalur.mzp` importer archive. Presence of the importer archive does not establish that 3ds Max is installed.

## Build and packaging flow

The current application uses C99, CMake/Ninja, the Android NDK, GLES 3 and a Lua 5.1.5 runtime. The build produces `libopem_amalur_scene.so`; a Python script packages the library and existing assets into an Android NativeActivity APK using `aapt2`, `zipalign` and `apksigner`.

```text
Recovered modules and generated asset snapshots from scene-v08
Scene geometry, collision and materials from scene-v17
Workbench, alchemy and room-lighting data from scene-v16-alchemy / scene-v18
                           +
work/v18-host C sources and earlier portable/runtime dependencies
                           |
                    CMake + Ninja + NDK
                           |
work/v18-host/build-android-arm64/libopem_amalur_scene.so
                           |
              work/v18-host/package_android.py
                           |
outputs/scene-v18/opem-amalur-scene-v0.14-arm64.apk
```

Build directories are `work\v18-host\build-windows` and `work\v18-host\build-android-arm64`. Android is `arm64-v8a`, with minimum API 26 and target API 35. The application package is `org.opemamalur.scene`.

These are the existing build commands **for a later authorized build**, not access checks:

```powershell
Set-Location 'C:\Users\rwill\Documents\Opem Amalur'
cmd.exe /d /c work\v18-host\build_validate.cmd
# Continue to packaging only if the build succeeded.
python work\v18-host\package_android.py
```

`build_validate.cmd` builds and runs the Windows input-test target, then configures/builds the Android `opem_amalur_scene` target. It is not a full project regression run. Packaging checks source/generated-input/library coherence, assembles the APK, requires the existing signing key, and verifies the signed payload. These commands write build artifacts and reports into existing stage paths; preserve the current checkpoint before a future changed build and keep builds/tests batched.

Important package inputs include:

- `outputs\scene-v08\modules\modules.tsv`, its Lua modules, `asset-macros.json`, `assets\` snapshots and `scene-final-windows.json` bootstrap report.
- `work\scene-inputs-v07\initial_0.pak\inputdeviceaction_init.bin`.
- `outputs\scene-v17\scene.bin`, `collision.bin`, `scene_materials.bin` and their source/evidence receipts.
- `outputs\scene-v18\Workbench.lua`, `workbench-integration.json`, `room-lighting.json` and current generated includes in `work\v18-host`.
- `outputs\scene-v16-alchemy\integration-data-receipt.json`.

The verified saved APK is 14,793,595 bytes, with SHA-256:

```text
c21a28119c261db065bc26e74f2339bec90ab6797e36b7f0277e1e3eb3184c21
```

Building, packaging and installing are separate steps. No install or device command is part of the access probe. The tablet may be connected to a different host; ADB being installed on Windows does not establish that Windows can see it.

## REA and native analysis access

The project wrapper is `C:\Users\rwill\Documents\Opem Amalur\rea.cmd`. It selects the project-local REA entrypoint, Ghidra provider, Ghidra directory, Java directory and a 900000 ms Ghidra startup timeout. REA's stdio MCP invocation is `rea.cmd mcp`.

A proposed configuration for a Claude client **running on Windows** with stdio MCP support is below. It has not been applied to Claude; use that client's supported configuration location and tool discovery. A Mac-hosted Claude process cannot directly execute these Windows paths.

```json
{
  "mcpServers": {
    "open-amalur-rea": {
      "command": "C:\\Program Files\\nodejs\\node.exe",
      "args": [
        "C:\\Users\\rwill\\Documents\\Opem Amalur\\tools\\rea\\node_modules\\rea-agents\\scripts\\rea.mjs",
        "mcp"
      ],
      "env": {
        "GHIDRA_INSTALL_DIR": "C:\\Users\\rwill\\Documents\\Opem Amalur\\tools\\ghidra_12.1.4_PUBLIC",
        "JAVA_HOME": "C:\\Users\\rwill\\Documents\\Opem Amalur\\tools\\jdk-21.0.13+9",
        "REA_ANALYSIS_PROVIDER": "ghidra",
        "REA_GHIDRA_STARTUP_TIMEOUT_MS": "900000"
      }
    }
  }
}
```

Past native sessions also used Windows-local Python workers which start REA over stdio, discover tool schemas and write results to the project. For example, `work\v18-lighting\scene_v18_session.py` used `work\scene-v18-requests\` and exported evidence under `outputs\scene-v18\rea-session-live\`. These are historical sessions. Do not rerun old workers as access checks: they use checkpoint-specific output directories, seeds and shutdown markers. Discover current tool schemas before a future analysis session.

The original target is:

```text
C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe
```

It is a 32-bit executable. The recorded target SHA-256 is `16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314`. The access probe checks only its presence. Preserve this input and the exported evidence. Original-game runtime captures require the appropriate interactive Windows/Steam session; an SSH terminal alone does not establish the correct desktop session.

## Reference projects

The complete Windows working folder retains all nine reference directories under `references\`:

```text
atom0s--depak
DevCortez--KoaModFramework
Doezer--KOARR-Modding
hardkiller2565123123--Kingdoms-of-Amalur-Re-Reckoning-coop-mod
Kender2--amalur
LukasCone-KOA-import
mark-mon--KoA-ReReckoning-VR
mburbea--ModelSwapper
ZucchiniZap--AmalurBxmlConverter
```

These contain archive/format/modding research and import/conversion references. The cleaned GitHub repository intentionally omits some reference trees; its `references/manifest.json` records upstream provenance. The complete private Windows checkpoint retains their source copies. Treat their existing notices and licenses separately from the project's authored code.

## Private files and project state

The existing signing key is `tools\android\opem-scene-debug.keystore`. Keep it: a replacement key would prevent an ordinary update over the current signed tablet app. The guide/probe reports its existence without reading its contents or publishing signing credentials.

The private native-game state backups are:

```text
work\v12-objects\native-state-before
work\v13-properties\native-state-before-cwd
work\v15-properties\native-state-before-interactive
```

Those 60 files and the signing key are excluded from the remote checkpoint. Their encrypted offline backup remains outstanding. Do not upload them to Git or replace/delete them during a tool-access check.

The latest completed scene has authored movement, static collision, a recovered Workbench Lua interaction and a first lighting pass. Exact native lighting, formula initialization/crafting and full-game behavior remain incomplete. The current task is tool access and documentation; it does not resume those engine tasks.

## Instructions to give Claude

> Check access to our existing Open Amalur Windows environment without modifying it. The complete working folder is `C:\Users\rwill\Documents\Opem Amalur` on `ROBMACHINEX`, reachable from the existing Mac account through SSH alias `open-rune-windows`. Read `OPEN_AMALUR_LOCAL_BUILD_GUIDE.md` in that folder, then run `python work\claude_access_probe.py` on Windows and report the machine name, missing paths, tool versions and APK hash match. If your environment cannot reach Windows, explain the missing connection or permission; do not treat GitHub repository access as local machine access. Do not build, install, launch the game, start native analysis, change tools or resume engine work. Keep the Windows working folder, signing key, save/config backups, tablet and historical artifacts unchanged.
