"""Run on Windows: bounded manifest/descriptor generation checks (no game execution)."""
import copy
import importlib.util
import json
import platform
import tempfile
from pathlib import Path

if __name__ == '__main__':
    if platform.system() != 'Windows':
        raise SystemExit('Run these checks on Windows')
    spec = importlib.util.spec_from_file_location('macro_generator', Path(__file__).with_name('generate_android_macro_table.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    checks = 0
    with tempfile.TemporaryDirectory(prefix='opem-macro-generator-') as temporary:
        manifest = Path(temporary) / 'macros.json'
        valid = [{'name': 'REGION_KEY', 'category': 69, 'file': 'region_init.bin', 'selection': 'explicit source'},
                 {'name': 'ABILITY_ID', 'category': 78, 'file': 'player_ability_init.bin'}]
        manifest.write_text(json.dumps(valid), encoding='utf-8')
        code, receipt_text = module.generate(manifest)
        receipt = json.loads(receipt_text)
        assert '{"region_init.bin", "REGION_KEY", 0x45}' in code
        assert '{"player_ability_init.bin", "ABILITY_ID", 0x4e}' in code
        assert receipt['macro_count'] == 2 and receipt['snapshot_count'] == 3
        checks += 3
        bad = [[], {}, valid * 17, [valid[0], valid[0]]]
        for field, value in [('name', 'bad-name'), ('name', 'A"B'), ('category', True),
                             ('category', 0), ('category', 256), ('category', '69'),
                             ('file', '../region.bin'), ('file', 'C:\\region.bin'),
                             ('file', 'bad".bin'), ('file', 'inputdeviceaction_init.bin')]:
            changed = copy.deepcopy(valid); changed[0][field] = value; bad.append(changed)
        for value in bad:
            manifest.write_text(json.dumps(value), encoding='utf-8')
            try:
                module.generate(manifest)
            except ValueError:
                checks += 1
            else:
                raise AssertionError('Accepted malformed manifest: ' + repr(value))
    print(json.dumps({'ok': True, 'checks': checks, 'scope': 'manifest-to-C descriptor validation only'}))
