"""Windows-only preflight: prevent packaging a stale descriptor binary or malformed snapshot."""
import argparse
import hashlib
import json
import platform
import struct
from pathlib import Path
from generate_android_macro_table import generate


def check_snapshot(path, enums=False):
    limit = 786444 if enums else 524296
    if path.stat().st_size > limit:
        raise ValueError('Snapshot exceeds admitted byte cap: ' + str(path))
    data = path.read_bytes()
    if enums:
        if len(data) < 12 or data[:4] != b'AENU':
            raise ValueError('Invalid enum header: ' + str(path))
        version, count = struct.unpack_from('<II', data, 4)
        if version != 1 or count > 65536 or len(data) != 12 + count * 12:
            raise ValueError('Invalid enum shape: ' + str(path))
        keys = [struct.unpack_from('<II', data, 12 + i * 12) for i in range(count)]
        if len(set(keys)) != count:
            raise ValueError('Duplicate enum hash pairs: ' + str(path))
    else:
        if len(data) < 8:
            raise ValueError('Invalid asset snapshot header: ' + str(path))
        version, count = struct.unpack_from('<II', data)
        if version != 1 or not 1 <= count <= 65536 or len(data) != 8 + count * 8:
            raise ValueError('Invalid asset snapshot shape: ' + str(path))
        ids = struct.unpack_from('<' + 'I' * count, data, 8)
        hashes = struct.unpack_from('<' + 'I' * count, data, 8 + count * 4)
        if 0 in ids or len(set(ids)) != count or len(set(hashes)) != count:
            raise ValueError('Invalid/duplicate asset IDs or hashes: ' + str(path))
    return {'file': path.name, 'bytes': len(data), 'count': count, 'sha256': hashlib.sha256(data).hexdigest()}


def main():
    if platform.system() != 'Windows':
        raise SystemExit('Run package preflight on Windows')
    p = argparse.ArgumentParser()
    p.add_argument('--project-root', type=Path, default=Path.home() / 'Documents/Opem Amalur')
    a = p.parse_args(); root = a.project_root
    scene = root / 'outputs/scene-v08'; build = root / 'work/v08-host/build-android-arm64'
    manifest = scene / 'asset-macros.json'
    generated, receipt_text = generate(manifest)
    if (build / 'generated/android_asset_macros.inc').read_text(encoding='utf-8') != generated:
        raise ValueError('Generated descriptor include is stale; rebuild Android')
    if (build / 'generated/android-macro-table.json').read_text(encoding='utf-8') != receipt_text:
        raise ValueError('Generated descriptor receipt is stale; rebuild Android')
    receipt = json.loads(receipt_text)
    library = build / 'libopem_amalur_scene.so'
    marker = ('opem-android-macro-manifest-sha256:' + receipt['source_manifest_sha256']).encode('ascii') + b'\0'
    if marker not in library.read_bytes():
        raise ValueError('Shared library does not contain the current compiled descriptor marker; rebuild before packaging')
    records = [check_snapshot(root / 'work/scene-inputs-v07/initial_0.pak/inputdeviceaction_init.bin'),
               check_snapshot(scene / 'assets/compiled_enums.bin', enums=True)]
    records.extend(check_snapshot(scene / 'assets' / m['file']) for m in receipt['macros'])
    if sum(r['bytes'] for r in records) > 16 * 1024 * 1024:
        raise ValueError('All setup snapshots together exceed Android host16MiB cap')
    result = {'ok': True, 'macro_count': receipt['macro_count'], 'snapshot_count': len(records),
              'descriptor_manifest_sha256': receipt['source_manifest_sha256'],
              'shared_library_sha256': hashlib.sha256(library.read_bytes()).hexdigest(),
              'snapshots': records, 'device_executed': False,
              'scope': 'Package-input structure and compiled descriptor coherence; not native mount selection proof'}
    (scene / 'android-package-input-preflight.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
