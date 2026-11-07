"""Read-only Open Amalur access probe. Run with the existing Windows Python."""
from pathlib import Path
import hashlib
import json
import os
import platform
import subprocess
import sys

ROOT = Path(r"C:\Users\rwill\Documents\Opem Amalur")
VS = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools")


def inspect_version(path, arguments):
    if not path.is_file():
        return {"path": str(path), "exists": False}
    result = subprocess.run(
        [str(path), *arguments], capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=15,
    )
    return {
        "path": str(path), "exists": True, "exit_code": result.returncode,
        "version_lines": (result.stdout + result.stderr).splitlines()[:3],
    }


def main():
    if platform.system() != "Windows":
        raise SystemExit("Run this probe on Windows. It does not test access from a cloud container.")
    tools = ROOT / "tools"
    required = [
        "src/amalur_script.py", "src/amalur_reconstruct.py", "tests",
        "work/CURRENT_STATE.txt", "work/v18-host/CMakeLists.txt",
        "work/v18-host/build_validate.cmd", "work/v18-host/package_android.py",
        "work/v18-host/room_lights.inc", "work/v18-host/integration_data.inc",
        "work/v08-portable/third_party/lua-5.1.5/src/lua.h",
        "work/v08-scene/package_readiness.py", "work/v09-textures", "work/v09-collision",
        "outputs/scene-v08/modules/modules.tsv", "outputs/scene-v08/asset-macros.json",
        "outputs/scene-v08/assets/compiled_enums.bin", "outputs/scene-v08/scene-final-windows.json",
        "work/scene-inputs-v07/initial_0.pak/inputdeviceaction_init.bin",
        "outputs/scene-v17/scene.bin", "outputs/scene-v17/collision.bin",
        "outputs/scene-v17/scene_materials.bin", "outputs/scene-v18/Workbench.lua",
        "outputs/scene-v18/room-lighting.json", "outputs/scene-v18/workbench-integration.json",
        "outputs/scene-v16-alchemy/integration-data-receipt.json",
        "tools/android/opem-scene-debug.keystore", "rea.cmd",
        "tools/rea/node_modules/rea-agents/scripts/rea.mjs",
        "tools/ghidra_12.1.4_PUBLIC/Ghidra/application.properties",
        "tools/android/sdk/android-35/android.jar", "tools/android/sdk/android-15/aapt2.exe",
        "tools/android/sdk/android-15/zipalign.exe", "tools/android/sdk/android-15/lib/apksigner.jar",
        "tools/android/android-ndk-r30/build/cmake/android.toolchain.cmake",
    ]
    checks = {rel: (ROOT / rel).exists() for rel in required}
    compiler_paths = [
        VS / "VC/Auxiliary/Build/vcvars64.bat",
        VS / "VC/Auxiliary/Build/vcvars32.bat",
        VS / "Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe",
        VS / "VC/Tools/MSVC/14.51.36231/bin/Hostx64/x64/cl.exe",
    ]
    compiler_checks = {str(p): p.exists() for p in compiler_paths}
    commands = [
        (Path(sys.executable), ["--version"]),
        (Path(r"C:\Program Files\nodejs\node.exe"), ["--version"]),
        (Path(r"C:\Program Files\Git\cmd\git.exe"), ["--version"]),
        (Path(r"C:\Program Files\CMake\bin\cmake.exe"), ["--version"]),
        (tools / "jdk-21.0.13+9/bin/java.exe", ["-version"]),
        (compiler_paths[2], ["--version"]),
        (tools / "android/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin/clang.exe", ["--version"]),
        (tools / "android/sdk/platform-tools/adb.exe", ["version"]),
    ]
    npm = []
    for folder, name in [("rea", "rea-agents"), ("rea-frida", "frida"), ("lua-validation", "luaparse")]:
        p = tools / folder / "node_modules" / name / "package.json"
        npm.append({"package": name, "path": str(p), "version": json.loads(p.read_text(encoding="utf-8"))["version"] if p.is_file() else None})
    apk = ROOT / "outputs/scene-v18/opem-amalur-scene-v0.14-arm64.apk"
    apk_info = {"path": str(apk), "exists": apk.is_file()}
    if apk.is_file():
        with apk.open("rb") as f:
            apk_info["sha256"] = hashlib.file_digest(f, "sha256").hexdigest()
        apk_info["matches_saved_v014"] = apk_info["sha256"] == "c21a28119c261db065bc26e74f2339bec90ab6797e36b7f0277e1e3eb3184c21"
    versions = [inspect_version(p, args) for p, args in commands]
    result = {
        "project": "Open Amalur", "machine": os.environ.get("COMPUTERNAME"),
        "user": os.environ.get("USERNAME"), "root": str(ROOT),
        "platform": platform.platform(), "read_only_probe": True,
        "project_paths": checks, "compiler_paths": compiler_checks,
        "missing_paths": [p for p, found in {**checks, **compiler_checks}.items() if not found],
        "tool_versions": versions, "npm_packages": npm,
        "python_local_distributions": sorted(p.name for p in (tools / "python-libs").glob("*.dist-info")),
        "original_game_executable_present": Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe").is_file(),
        "working_folder_is_git_clone": (ROOT / ".git").exists(),
        "saved_apk": apk_info,
        "writes_builds_installs_or_device_commands_performed": False,
    }
    print(json.dumps(result, indent=2, ensure_ascii=True))
    ok = not result["missing_paths"] and all(v.get("exit_code") == 0 for v in versions) and all(p["version"] for p in npm)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
