"""Generate the Android descriptor table from the same explicit manifest as APK packaging."""
import argparse
import hashlib
import json
import re
from pathlib import Path


def generate(manifest: Path):
    raw = manifest.read_bytes()
    entries = json.loads(raw.decode('utf-8-sig'))
    if not isinstance(entries, list) or not 1 <= len(entries) <= 32:
        raise ValueError('Manifest must contain 1..32 explicit macros')
    names = set()
    rows = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError('Macro entry must be an object')
        name, category, filename = entry.get('name'), entry.get('category'), entry.get('file')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Z_][A-Z_0-9]{0,126}', name) or name in names:
            raise ValueError('Invalid or repeated macro name')
        if type(category) is not int or not 1 <= category <= 255:
            raise ValueError('Explicit integer category1..255 required')
        if not isinstance(filename, str) or not re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_.-]*\.bin', filename):
            raise ValueError('Snapshot must use a safe .bin basename')
        if filename == 'inputdeviceaction_init.bin':
            raise ValueError('Input actions use their separate installer')
        names.add(name)
        rows.append({'name': name, 'category': category, 'file': filename})
    digest = hashlib.sha256(raw).hexdigest()
    lines = ['/* Generated from asset-macros.json; edit the manifest, not this file. */',
             '#define OPEM_ANDROID_MACRO_MANIFEST_SHA256 "' + digest + '"',
             'static const snapshot_descriptor snapshot_descriptors[] = {',
             '    {"inputdeviceaction_init.bin", NULL, 0},']
    for row in rows:
        lines.append('    {"%s", "%s", 0x%02x},' % (row['file'], row['name'], row['category']))
    lines += ['};', '']
    receipt = {'schema': 1, 'source_manifest_sha256': digest, 'macro_count': len(rows),
               'snapshot_count': len(rows) + 1, 'macros': rows,
               'scope': 'Explicit manifest mappings only; no inferred native catalog categories'}
    return '\n'.join(lines), json.dumps(receipt, indent=2) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--check', action='store_true', help='Reject stale generated files without changing them')
    args = parser.parse_args()
    code, receipt = generate(args.manifest)
    for path, expected in [(args.output, code), (args.receipt, receipt)]:
        if args.check:
            if not path.is_file() or path.read_text(encoding='utf-8') != expected:
                raise SystemExit('Stale/missing generated macro table: ' + str(path))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding='utf-8', newline='\n')
    print(json.dumps({'ok': True, 'mode': 'check' if args.check else 'generate',
                      'macro_count': json.loads(receipt)['macro_count']}))


if __name__ == '__main__':
    main()
