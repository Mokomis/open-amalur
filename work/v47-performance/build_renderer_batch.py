"""Build both renderer targets once after a batch of edits; pin package inputs."""
from pathlib import Path
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
import time

P = Path(__file__).resolve().parents[2]
V = P / 'work/v47-performance'
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
out = V / 'build-receipts' / stamp

def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def main():
    # Do not interrupt an interactive preview or fail halfway through replacing its executable.
    listing = subprocess.check_output(
        ['tasklist', '/FI', 'IMAGENAME eq open-amalur-windows.exe', '/FO', 'CSV', '/NH'],
        text=True,
    )
    if 'open-amalur-windows.exe' in listing.lower():
        raise SystemExit('Close the custom Windows preview before building. Original game is untouched.')
    out.mkdir(parents=True, exist_ok=False)
    exe = P / 'work/v40-windows-host/build/open-amalur-windows.exe'
    arm = P / 'work/v19-host/build-android-arm64/libopem_amalur_scene.so'
    receipt_path = V / 'final-renderer-build.json'
    for path in [exe, arm, receipt_path]:
        if path.exists():
            shutil.copy2(path, out / ('before-' + path.name))
    inputs = sorted(f for f in (P / 'work/v19-host').iterdir() if f.suffix in ['.c', '.h', '.inc'])
    recipe_names = ['work/v19-host/CMakeLists.txt', 'work/v40-windows-host/CMakeLists.txt']
    before = {f.name: sha(f) for f in inputs}
    recipes = {name: sha(P / name) for name in recipe_names}
    record = {}
    for label, argv in [
        ('windows', ['cmd.exe', '/c', str(P / 'work/v40-windows-host/build.cmd')]),
        ('android', [r'C:\Program Files\CMake\bin\cmake.exe', '--build',
                     str(P / 'work/v19-host/build-android-arm64'), '--target',
                     'opem_amalur_scene', '--parallel', '8']),
    ]:
        start = time.monotonic()
        result = subprocess.run(argv, capture_output=True, cwd=P)
        (out / (label + '.log')).write_bytes(result.stdout + result.stderr)
        record[label] = {'exit': result.returncode, 'seconds': time.monotonic() - start}
        if label == 'windows':
            for name in ['build.log', 'compiler.log', 'configure.log', 'imports.log']:
                log = P / 'work/v40-windows-host' / name
                if log.exists():
                    shutil.copy2(log, out / ('windows-' + name))
    after_inputs = sorted(f for f in (P / 'work/v19-host').iterdir() if f.suffix in ['.c', '.h', '.inc'])
    record['sources'] = {f.name: sha(f) for f in after_inputs}
    record['recipes'] = {name: sha(P / name) for name in recipe_names}
    record['inputs_stable_during_build'] = before == record['sources'] and recipes == record['recipes']
    if not record['inputs_stable_during_build']:
        record['windows']['exit'] = record['android']['exit'] = 1
        record['failure'] = 'Source changed during compilation. Finish concurrent edits and run one batch.'
    if exe.exists():
        record['windows_exe_sha256'] = sha(exe)
    if arm.exists():
        record['android_library_sha256'] = sha(arm)
    record['logs_and_prior_artifacts'] = str(out)
    payload = json.dumps(record, indent=2).encode('utf-8')
    (out / 'receipt.json').write_bytes(payload)
    tmp = receipt_path.with_suffix('.new.json')
    tmp.write_bytes(payload)
    tmp.replace(receipt_path)
    print(json.dumps({k: record[k] for k in ['windows', 'android', 'inputs_stable_during_build',
                                           'logs_and_prior_artifacts']}, indent=2))
    return 0 if all(record[k]['exit'] == 0 for k in ['windows', 'android']) else 1

if __name__ == '__main__':
    sys.exit(main())
