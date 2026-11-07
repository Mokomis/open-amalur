"""Windows-only synthetic packaging gates; never executes fixture files as programs."""
import hashlib
import json
import os
import platform
import tempfile
from pathlib import Path
from package_readiness import inspect_inputs, CORE


def make(root):
    out=root/'outputs/scene-v08'; modules=out/'modules'; runtime=root/'work/v08-portable/runtime'
    modules.mkdir(parents=True);runtime.mkdir(parents=True);(out/'assets').mkdir()
    (root/'work/v08-scripts').mkdir(parents=True);(root/'work/v08-scripts/module_source_adapter.py').write_text('# fixture adapter\n')
    (root/'work/v08-portable/build-windows').mkdir();(root/'work/v08-portable/build-windows/amalur-scene-v08-inspect.exe').write_bytes(b'fixture identity only, never executed')
    records=[]
    for index,name in enumerate(['ParentUtils','SpaceCommon']):
        path=modules/(name+'.lua');path.write_text('return {}\n')
        records.append({'module':name,'source_file':path.name,'adapted_source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'function_bodies':index+1})
    manifest=modules/'modules.tsv';manifest.write_text('ParentUtils\tParentUtils.lua\nSpaceCommon\tSpaceCommon.lua\n')
    for name in CORE:(runtime/name).write_text('return {}\n')
    macro=[{'name':'LOOT_TABLE_ID','category':55,'file':'loottable_init.bin'}]
    (out/'asset-macros.json').write_text(json.dumps(macro))
    snapshot=root/'work/scene-inputs-v07/initial_0.pak/inputdeviceaction_init.bin';snapshot.parent.mkdir(parents=True);snapshot.write_bytes(b'fixture-input')
    (out/'assets/compiled_enums.bin').write_bytes(b'fixture-enums');(out/'assets/loottable_init.bin').write_bytes(b'fixture-loot')
    inventory={'registered_modules':2,'function_bodies':3,'missing':[],'modules':records,'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest(),'source_adapter_sha256':hashlib.sha256((root/'work/v08-scripts/module_source_adapter.py').read_bytes()).hexdigest()}
    (modules/'module-inventory.json').write_text(json.dumps(inventory))
    report={'ok':True,'phase':'complete','bootstrap_loaded':True,'root_loaded':True,'event_invoked':True,'event_argument_count':0,'registered_modules':2,'asset_macro_count':1,'instruction_budget':30000000,'controller_state_mode':'android-logical-standard','optional_content_mode':'known-empty','platform_mode':'android','profile_mode':'fresh-session-memory','quick_save_mode':'unsupported','language_catalog_mode':'known-empty-host-Automatic','renderer_max_anisotropy':1,'error':''}
    report['lua_memory_limit_bytes']=256*1024*1024;report['resource_limit_bytes']=128*1024*1024
    report['resource_bytes']=sum(p.stat().st_size for p in [manifest,*runtime.glob('*.lua'),*modules.glob('*.lua')])
    report['asset_snapshot_bytes']=sum(p.stat().st_size for p in [snapshot,* (out/'assets').glob('*.bin')])
    destination=out/'scene-final-windows.json';destination.write_text(json.dumps(report))
    for path in root.rglob('*'):
        if path.is_file():os.utime(path,(1000,1000))
    os.utime(destination,(2000,2000))
    return destination


if __name__=='__main__':
    if platform.system()!='Windows':raise SystemExit('Run these authored packaging fixtures on Windows')
    checks=0
    with tempfile.TemporaryDirectory(prefix='opem-package-readiness-') as base:
        root=Path(base)/'valid';receipt=make(root);pairs,info=inspect_inputs(root,receipt)
        assert set(pairs)=={'ParentUtils','SpaceCommon'} and info['recovered_function_bodies']==3;checks+=1
        for key,value in [('ok',False),('bootstrap_loaded',False),('registered_modules',3),('asset_macro_count',2),('instruction_budget',10000000),('lua_memory_limit_bytes',128*1024*1024),('resource_limit_bytes',64*1024*1024),('renderer_max_anisotropy',16),('platform_mode','win32'),('resource_bytes',1),('asset_snapshot_bytes',1)]:
            current=Path(base)/(key+'-bad');receipt=make(current);data=json.loads(receipt.read_text());data[key]=value;receipt.write_text(json.dumps(data))
            try:inspect_inputs(current,receipt)
            except ValueError:checks+=1
            else:raise AssertionError('Accepted bad receipt '+key)
        for label in ['module-hash','duplicate-module','stale-input']:
            current=Path(base)/label;receipt=make(current)
            if label=='module-hash':(current/'outputs/scene-v08/modules/SpaceCommon.lua').write_text('return false\n')
            elif label=='duplicate-module':
                path=current/'outputs/scene-v08/modules/modules.tsv';path.write_text(path.read_text()+'SpaceCommon\tSpaceCommon.lua\n')
            else:os.utime(current/'work/v08-portable/runtime/amalur_uint64.lua',(3000,3000))
            try:inspect_inputs(current,receipt)
            except ValueError:checks+=1
            else:raise AssertionError('Accepted '+label)
    print(json.dumps({'ok':True,'checks':checks,'scope':'Packaging readiness gates only; synthetic data, no program/device execution'}))
