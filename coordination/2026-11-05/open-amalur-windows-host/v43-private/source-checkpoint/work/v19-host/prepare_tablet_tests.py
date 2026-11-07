"""Windows-only build/stage of real arm64 test executables; never invokes adb/device commands."""
import argparse
import datetime
import hashlib
import json
import platform
import re
import shlex
import shutil
import struct
import subprocess
import tarfile
from pathlib import Path

BASE_TESTS = [
    ('controller', 'amalur-controller-state-test', ['runtime'], 119),
    ('layout', 'amalur-android-layout-test', ['runtime'], 97),
    ('content', 'amalur-content-state-test', ['runtime'], 460),
    ('platform', 'amalur-platform-state-test', ['runtime'], 24),
    ('fresh', 'amalur-fresh-profile-test', ['runtime'], 105),
    ('quicksave', 'amalur-quick-save-state-test', ['runtime'], 24),
    ('asset', 'amalur-asset-macro-test', ['runtime', 'assets/loottable_init.bin'], 44),
    ('playerregistry', 'amalur-player-registry-test', ['runtime'], 3042),
    ('enums', 'amalur-enum-snapshot-test', ['runtime'], 64),
    ('renderer', 'amalur-renderer-cap-test', ['runtime'], 34),
    ('languages', 'amalur-language-catalog-test', ['runtime'], 52),
    ('type11', 'amalur-module-inspect', ['--runtime-dir', 'runtime', '--manifest',
                                      'type11/modules.tsv', '--module', 'Type11TabletHarness'], None),
    ('readproxy', 'amalur-module-inspect', ['--runtime-dir', 'runtime', '--manifest', 'readproxy/modules.tsv', '--module', 'ReadProxyTabletHarness'], None),
    ('gc', 'amalur-lua-weak-mode-test', ['fixtures/lua_weak_mode_test.lua'], None),
]
SYSTEM_LIBRARIES = {'libc.so', 'libm.so', 'libdl.so', 'liblog.so', 'libandroid.so'}


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(value):
    p = Path(value)
    if not value or p.is_absolute() or any(part in ('', '.', '..') for part in value.split('/')) or '\\' in value or ':' in value:
        raise ValueError('Bundle path must be relative and traversal-free: ' + value)
    if not re.fullmatch(r'[A-Za-z0-9_./-]+', value):
        raise ValueError('Unsupported bundle filename: ' + value)
    return p


def main():
    if platform.system() != 'Windows':
        raise SystemExit('Run on Windows; this script builds/stages arm64 tests but does not execute them')
    parser = argparse.ArgumentParser()
    parser.add_argument('--project-root', type=Path, default=Path.home() / 'Documents/Opem Amalur')
    parser.add_argument('--build-dir', type=Path, help='Configured Android CMake root; default v08-host/build-android-arm64')
    parser.add_argument('--output', type=Path, help='New directory; existing paths are refused')
    parser.add_argument('--no-build', action='store_true', help='Stage existing binaries; hashes still recorded')
    parser.add_argument('--timeout-seconds', type=int, default=120)
    parser.add_argument('--extra-test-spec', type=Path, help='JSON list of name,target,args,expected_checks for later services')
    parser.add_argument('--extra-file', type=Path, nargs=2, action='append', default=[], metavar=('SOURCE', 'BUNDLE_PATH'))
    args = parser.parse_args()
    if not 1 <= args.timeout_seconds <= 600:
        raise SystemExit('Timeout must be1..600 seconds per test')
    root = args.project_root.resolve()
    build = (args.build_dir or root / 'work/v08-host/build-android-arm64').resolve()
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = (args.output or root / 'outputs/scene-v08' / ('tablet-tests-' + stamp)).resolve()
    output.mkdir(parents=True, exist_ok=False)
    tests = [dict(name=n, target=t, args=a, expected_checks=c) for n, t, a, c in BASE_TESTS]
    if args.extra_test_spec:
        tests.extend(json.loads(args.extra_test_spec.read_text(encoding='utf-8-sig')))
    names = set()
    for test in tests:
        if not isinstance(test, dict) or not re.fullmatch(r'[a-zA-Z0-9_-]+', test.get('name', '')) or test['name'] in names:
            raise ValueError('Invalid or duplicate test name')
        names.add(test['name'])
        if not re.fullmatch(r'[a-zA-Z0-9_-]+', test.get('target', '')):
            raise ValueError('Invalid target name')
        if not isinstance(test.get('args'), list) or not all(isinstance(x, str) and '\x00' not in x for x in test['args']):
            raise ValueError('Test args must be literal strings')
        count = test.get('expected_checks')
        if count is not None and (type(count) is not int or count < 1):
            raise ValueError('Invalid expected check count')
    cache = build / 'CMakeCache.txt'
    if not cache.is_file():
        raise ValueError('Configure the Android build before generating the bundle')
    cache_text = cache.read_text(encoding='utf-8', errors='replace')
    if not re.search(r'^(?:ANDROID_ABI|CMAKE_ANDROID_ARCH_ABI):[^=]*=arm64-v8a$', cache_text, re.M):
        raise ValueError('Configured build must explicitly target arm64-v8a')
    targets = list(dict.fromkeys(test['target'] for test in tests))
    if not args.no_build:
        proc = subprocess.run(['cmake', '--build', str(build), '--parallel', '8', '--target', *targets],
                              capture_output=True, timeout=1800)
        (output / 'build.log').write_bytes(proc.stdout + proc.stderr)
        if proc.returncode:
            raise SystemExit('Android test build failed; see ' + str(output / 'build.log'))
    records = {}

    def copy(source, destination):
        destination = safe_relative(destination)
        source = source.resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        target = output / destination
        if target.exists():
            raise ValueError('Duplicate bundle destination: ' + str(destination))
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        records[destination.as_posix()] = {'sha256': sha(target), 'bytes': target.stat().st_size,
                                         'source': str(source)}
        return target

    readelf = root / 'tools/android/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-readelf.exe'
    elf_records = []
    for target_name in targets:
        candidates = [p for p in (build / 'portable' / target_name, build / target_name) if p.is_file()]
        if len(candidates) != 1:
            raise ValueError('Expected exactly one built ELF for ' + target_name)
        executable = candidates[0]
        with executable.open('rb') as stream:
            header = stream.read(64)
        if len(header) < 64 or header[:6] != b'\x7fELF\x02\x01' or struct.unpack_from('<HH', header, 16) != (3, 183):
            raise ValueError('Expected arm64 little-endian PIE ELF, not Windows executable: ' + str(executable))
        proc = subprocess.run([str(readelf), '-d', str(executable)], capture_output=True, timeout=30)
        if proc.returncode:
            raise ValueError('ELF dependency inspection failed: ' + target_name)
        dependencies = re.findall(r'\(NEEDED\).*\[([^]]+)\]', proc.stdout.decode('utf-8', errors='replace'))
        if set(dependencies) - SYSTEM_LIBRARIES:
            raise ValueError('Unbundled non-system ELF dependencies for %s: %s' % (target_name, dependencies))
        copy(executable, 'bin/' + target_name)
        elf_records.append({'target': target_name, 'needed': dependencies})
    runtime = root / 'work/v08-portable/runtime'
    core = ['amalur_uint64.lua', 'amalur_engine_handles.lua', 'engine_binding_registry.lua',
            'amalur_engine_bindings.lua', 'amalur_native_math.lua']
    for filename in core:
        copy(runtime / filename, 'runtime/' + filename)
    copy(root / 'outputs/scene-v08/assets/loottable_init.bin', 'assets/loottable_init.bin')
    copy(root / 'work/v08-portable/tests/lua_weak_mode_test.lua', 'fixtures/lua_weak_mode_test.lua')
    fixture = root / 'outputs/scene-v08/type11-key-tests'
    provenance = json.loads((fixture / 'provenance.json').read_text(encoding='utf-8-sig'))
    if provenance.get('carrier_sha256') != sha(runtime / 'amalur_uint64.lua'):
        raise ValueError('Type11 fixture carrier differs from bundled runtime; regenerate fixture on Windows')
    if provenance.get('adapter_sha256') != sha(root / 'work/v08-scripts/module_source_adapter.py'):
        raise ValueError('Type11 fixture adapter is stale; regenerate fixture on Windows')
    harness = fixture / 'type11-key-harness.lua'
    if provenance.get('files', {}).get(harness.name) != sha(harness):
        raise ValueError('Type11 harness hash does not match its generation receipt')
    copy(harness, 'type11/type11-key-harness.lua')
    copy(fixture / 'provenance.json', 'type11/provenance.json')
    (output / 'type11/tablet-wrapper.lua').write_text(
        "local n=require('Type11KeyHarness');assert(type(n)=='number' and n>0);print('type11 key assertions: '..n);return n\n", encoding='utf-8', newline='\n')
    (output / 'type11/modules.tsv').write_text('Type11KeyHarness\ttype11-key-harness.lua\nType11TabletHarness\ttablet-wrapper.lua\n', encoding='utf-8', newline='\n')
    proxy = root / 'outputs/scene-v08/read-proxy-tests'
    proxy_receipt = json.loads((proxy / 'provenance.json').read_text(encoding='utf-8-sig'))
    if proxy_receipt.get('adapter_sha256') != sha(root / 'work/v08-scripts/module_source_adapter.py'):
        raise ValueError('Read-proxy fixture adapter is stale')
    for filename in ['read-proxy-harness.lua', 'read-guard-module.lua']:
        if proxy_receipt.get('files', {}).get(filename) != sha(proxy / filename):
            raise ValueError('Read-proxy fixture hash mismatch')
        copy(proxy / filename, 'readproxy/' + filename)
    copy(proxy / 'provenance.json', 'readproxy/provenance.json')
    (output / 'readproxy/tablet-wrapper.lua').write_text("local n=require('ReadProxyHarness');assert(type(n)=='number' and n>0);print('read proxy assertions: '..n);return n\n", encoding='utf-8', newline='\n')
    (output / 'readproxy/modules.tsv').write_text('ReadGuardModule\tread-guard-module.lua\nReadProxyHarness\tread-proxy-harness.lua\nReadProxyTabletHarness\ttablet-wrapper.lua\n', encoding='utf-8', newline='\n')
    for source, destination in args.extra_file:
        copy(source, destination.as_posix())
    lines = ['#!/system/bin/sh', 'set -eu', 'cd "$(dirname "$0")"', 'export LC_ALL=C',
             'command -v timeout >/dev/null || { echo "Android timeout command required"; exit 2; }',
             'sha256sum -c SHA256SUMS || exit 2', 'chmod 700 bin/*',
             'result_dir="results-$(date -u +%Y%m%dT%H%M%SZ)-$$"', 'mkdir "$result_dir"',
             'failures=0', 'run_test() {', '  name="$1"; pattern="$2"; shift 2',
             '  status=0', '  if timeout ' + str(args.timeout_seconds) + ' "$@" >"$result_dir/$name.log" 2>&1; then :; else status=$?; fi',
             '  if [ "$status" -eq 0 ] && [ -n "$pattern" ] && ! grep -Eq "$pattern" "$result_dir/$name.log"; then status=125; fi',
             '  printf "%s\\t%s\\n" "$name" "$status" >>"$result_dir/status.tsv"',
             '  cat "$result_dir/$name.log"', '  if [ "$status" -ne 0 ]; then failures=$((failures+1)); fi', '}', '']
    for test in tests:
        count = test.get('expected_checks')
        pattern = '"checks"[[:space:]]*:[[:space:]]*' + str(count) + '([,}])' if count else ''
        command = ['run_test', test['name'], pattern, './bin/' + test['target'], *test['args']]
        lines.append(' '.join(shlex.quote(x) for x in command))
    lines += ['printf "failures=%s\\n" "$failures" | tee "$result_dir/summary.txt"',
              '[ "$failures" -eq 0 ]', '']
    (output / 'run-tests.sh').write_text('\n'.join(lines), encoding='utf-8', newline='\n')
    (output / 'README.txt').write_text(
        'Private arm64 tablet test bundle. No APK installation or user save/profile access.\n'
        'Copy this directory to a NEW dedicated /data/local/tmp/opem-v08-tests-<unique> path.\n'
        'Run: adb shell sh /data/local/tmp/opem-v08-tests-<unique>/run-tests.sh\n'
        'Use an explicit adb device serial when more than one device is present.\n'
        'The runner verifies hashes, sets execute mode only on its bundled test binaries,\n'
        'and writes results only under this bundle. It does not install/uninstall apps,\n'
        'clear app data, touch original game files, or delete previous test results.\n'
        'Copy results-* back for review. Nonzero exit includes failed assertions,\n'
        'timeouts, or changed historical check counts requiring review.\n'
        'These are portable-library fixtures, not Android Activity/render/controller tests.\n', encoding='utf-8', newline='\n')
    sources = [root / 'work/v08-portable/CMakeLists.txt', root / 'work/v08-portable/src/amalur_runtime.c',
               root / 'work/v08-portable/src/scene_profile_v08.c', root / 'work/v08-portable/src/scene_asset_macros_v08.c',
               root / 'work/v08-portable/src/scene_enums_v08.c',
               root / 'work/v08-portable/third_party/lua-5.1.5/src/lgc.c']
    manifest = {'schema': 1, 'created_utc': stamp, 'device_executed': False, 'abi': 'arm64-v8a',
                'build_dir': str(build), 'built_now': not args.no_build, 'cmake_cache_sha256': sha(cache),
                'tests': tests, 'elf': elf_records, 'copied_files': records,
                'source_hashes': {str(p.relative_to(root)): sha(p) for p in sources},
                'scope': 'Library fixture bundle; no claim of Activity/gameplay/graphics verification'}
    (output / 'bundle-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    paths = sorted(p for p in output.rglob('*') if p.is_file())
    (output / 'SHA256SUMS').write_text(''.join(sha(p) + '  ' + p.relative_to(output).as_posix() + '\n' for p in paths), encoding='ascii', newline='\n')
    archive = output.with_name(output.name + '.tar.gz')
    with tarfile.open(archive, 'x:gz') as tar:
        for path in sorted(p for p in output.rglob('*') if p.is_file()):
            info = tar.gettarinfo(str(path), arcname=output.name + '/' + path.relative_to(output).as_posix())
            info.mode = 0o700 if path.parent.name == 'bin' or path.name == 'run-tests.sh' else 0o600
            with path.open('rb') as stream:
                tar.addfile(info, stream)
    print(json.dumps({'ok': True, 'bundle': str(output), 'archive': str(archive),
                      'archive_sha256': sha(archive), 'tests': len(tests), 'device_executed': False}, indent=2))


if __name__ == '__main__':
    main()
