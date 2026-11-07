"""Read-only package readiness checks; does not execute recovered scripts or device tools."""
import hashlib
import json
from pathlib import Path

CORE = ('amalur_uint64.lua', 'amalur_engine_handles.lua', 'engine_binding_registry.lua',
        'amalur_engine_bindings.lua', 'amalur_native_math.lua')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_inputs(root: Path, bootstrap_report: Path):
    out = root / 'outputs/scene-v08'
    modules = out / 'modules'
    manifest = modules / 'modules.tsv'
    pairs = {}
    for line in manifest.read_text(encoding='utf-8-sig').splitlines():
        if not line or line.startswith('#'):
            continue
        parts = line.split('\t')
        if len(parts) != 2:
            raise ValueError('Module manifest requires name<TAB>basename')
        name, filename = parts
        if (not name or len(name.encode('utf-8')) > 255 or name in pairs or
                any(ord(c) < 32 or c in '/\\:' for c in name)):
            raise ValueError('Invalid/duplicate module name: ' + repr(name))
        if not filename or filename in ('.', '..') or any(c in filename for c in '/\\:'):
            raise ValueError('Module filename must be a manifest-local basename')
        pairs[name] = filename
    if not {'ParentUtils', 'SpaceCommon'} <= set(pairs):
        raise ValueError('Current Android bootstrap requires exact ParentUtils and SpaceCommon entries')
    inventory_path = modules / 'module-inventory.json'
    inventory = json.loads(inventory_path.read_text(encoding='utf-8-sig'))
    records = inventory.get('modules', [])
    if (inventory.get('registered_modules') != len(pairs) or len(records) != len(pairs) or
            inventory.get('manifest_sha256') != sha(manifest)):
        raise ValueError('Module inventory does not match current manifest')
    if inventory.get('missing'):
        raise ValueError('Module inventory still has missing required entries')
    adapter = root / 'work/v08-scripts/module_source_adapter.py'
    if inventory.get('source_adapter_sha256') != sha(adapter):
        raise ValueError('Module adapter changed since the recorded adaptation; regenerate from frozen originals')
    seen = set(); function_count = 0
    for record in records:
        name = record.get('module'); filename = record.get('source_file')
        if name in seen or pairs.get(name) != filename:
            raise ValueError('Module record identity differs from manifest')
        seen.add(name)
        if record.get('adapted_source_sha256') != sha(modules / filename):
            raise ValueError('Adapted source hash mismatch: ' + str(name))
        count = record.get('function_bodies')
        if type(count) is not int or count < 0:
            raise ValueError('Missing/invalid module function count: ' + str(name))
        function_count += count
    if inventory.get('function_bodies') != function_count:
        raise ValueError('Inventory function total differs from its module records')
    macros_path = out / 'asset-macros.json'
    macros = json.loads(macros_path.read_text(encoding='utf-8-sig'))
    report = json.loads(bootstrap_report.read_text(encoding='utf-8-sig'))
    expected = {'ok': True, 'phase': 'complete', 'bootstrap_loaded': True,
                'root_loaded': True, 'event_invoked': True, 'event_argument_count': 0,
                'registered_modules': len(pairs), 'asset_macro_count': len(macros),
                'instruction_budget': 30000000, 'lua_memory_limit_bytes': 256*1024*1024,
                'resource_limit_bytes': 128*1024*1024, 'controller_state_mode': 'android-logical-standard',
                'optional_content_mode': 'known-empty', 'platform_mode': 'android',
                'profile_mode': 'fresh-session-memory', 'quick_save_mode': 'unsupported',
                'language_catalog_mode': 'known-empty-host-Automatic', 'renderer_max_anisotropy': 1}
    for key, value in expected.items():
        if report.get(key) != value:
            raise ValueError('Bootstrap readiness mismatch %s: expected%r got%r' % (key, value, report.get(key)))
    if report.get('error'):
        raise ValueError('Bootstrap report still records an error')
    runtime = root / 'work/v08-portable/runtime'
    sources = [runtime / name for name in CORE] + [manifest] + [modules / filename for filename in pairs.values()]
    if report.get('resource_bytes') != sum(path.stat().st_size for path in sources):
        raise ValueError('Bootstrap resource-byte total differs from current inputs')
    snapshots = [root / 'work/scene-inputs-v07/initial_0.pak/inputdeviceaction_init.bin', out / 'assets/compiled_enums.bin']
    snapshots += [out / 'assets' / row['file'] for row in macros]
    if report.get('asset_snapshot_bytes') != sum(path.stat().st_size for path in snapshots):
        raise ValueError('Bootstrap snapshot-byte total differs from current selected catalogs')
    # Local workflow freshness guard, not a claim that the native inspector
    # itself emitted cryptographic input identities. Record exact hashes below.
    inputs = [*sources, *snapshots, inventory_path, macros_path, adapter,
              root / 'work/v08-portable/build-windows/amalur-scene-v08-inspect.exe']
    if any(path.stat().st_mtime_ns > bootstrap_report.stat().st_mtime_ns for path in inputs):
        raise ValueError('An inspector/input changed after the final bootstrap report; rerun final Windows bootstrap')
    details = {'bootstrap_report': str(bootstrap_report), 'bootstrap_report_sha256': sha(bootstrap_report),
               'readiness_checks': 'success/policies/counts/byte totals/metadata hashes/local input freshness',
               'bootstrap_report_emits_input_hashes': False,
               'registered_modules': len(pairs), 'recovered_function_bodies': function_count,
               'asset_macro_count': len(macros), 'lua_memory_bytes': report.get('lua_memory_bytes'),
               'required_bootstrap_module': 'ParentUtils', 'root_module': 'SpaceCommon',
               'event': 'on_object_creation_complete', 'instruction_budget': 30000000,
               'lua_memory_limit_bytes': 256*1024*1024, 'resource_limit_bytes': 128*1024*1024,
               'input_hashes': {str(p.relative_to(root)): sha(p) for p in dict.fromkeys(inputs)},
               'scope': 'Portable bootstrap readiness only; actual installed APK execution remains separate'}
    return pairs, details
