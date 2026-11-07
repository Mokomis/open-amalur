"""Build metadata from Windows-produced descriptor evidence, never PE bytes.

Run from this directory on either host after mirroring derived reports.
Namespace association remains explicit inference until its owner trace arrives.
"""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHA = '16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
SPECS = [('QUEST', 'quest-descriptors.json', 48), ('GAME', 'game-descriptors.json', 165),
         ('ACTOR', 'actor-descriptors.json', 611), ('TIME', 'time-descriptors.json', 6),
         ('WINDOW', 'window-descriptors.json', 232)]
OWNERS = {
    'QUEST': {'vtable': '0x174da98', 'getter': '0xec83d0', 'getter_slot': '0x174daa4', 'registration_slot': '0x174daac', 'owner': 'BHG::LuaQuestServices', 'evidence': ['v06-binding-vtable.json', 'quest_namespace_refs.json', 'quest_table_constructor_refs.json', 'quest_owner_initializer.json', 'engine_namespace_installation.json']},
    'GAME': {'vtable': '0x174a598', 'getter': '0xea40e0', 'getter_slot': '0x174a5a4', 'registration_slot': '0x174a5ac', 'evidence': ['game_namespace_getter_refs.json', 'game_table_constructor_refs.json']},
    'ACTOR': {'vtable': '0x174dac0', 'getter': '0xec84a0', 'getter_slot': '0x174dacc', 'registration_slot': '0x174dad4', 'owner': 'BHG::LuaActorServices', 'evidence': ['v06-actor-vtable.json', 'engine_namespace_installation.json']},
    'TIME': {'vtable': '0x17549a0', 'getter': '0xeedde0', 'getter_slot': '0x17549ac', 'registration_slot': '0x17549b4', 'evidence': ['v06-actor-stack-probe.json', 'time_namespace_getter_refs.json']},
    'WINDOW': {'vtable': '0x17366a0', 'getter': '0xc082b0', 'getter_slot': '0x17366ac', 'registration_slot': '0x17366b4', 'evidence': ['v06-window-and-argcheck.json', 'window_namespace_getter_refs.json']}}
report = {'schema_version': 1, 'target_sha256': SHA,
          'scope': 'Static name/address registry. Direct service-record to native C-closure bridge is documented in native-binding-abi.json. No engine implementation or runtime parity is implied; callback addresses require initialized native engine state and are reference metadata only.',
          'namespaces': {}, 'missing_namespaces': []}
lua = ['-- Generated from Windows native descriptor evidence; addresses are metadata only.',
       '-- No game function is called by loading this registry.', 'return {']
for namespace, filename, count in SPECS:
    path = HERE / filename
    if not path.exists():
        report['missing_namespaces'].append(namespace)
        continue
    evidence = json.loads(path.read_text(encoding='utf-8'))
    assert evidence['target_sha256'] == SHA
    rows = evidence['descriptors']
    assert len(rows) == count, (namespace, len(rows), count)
    assert len({row['name'] for row in rows}) == count
    assert all(row['callback'] is not None for row in rows)
    assert all(row['callback_stack_offset'] == row['name_object_stack_offset'] + 12 for row in rows)
    report['namespaces'][namespace] = {
        'registration_function': evidence['entry'], 'count': count,
        'descriptor_evidence': filename,
        'descriptor_evidence_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'namespace_association': 'Namespace-name getter and method initializer share the observed owner vtable layout. Generic service-record to C-closure dispatch is traced; full per-namespace bootstrap/runtime installation remains unobserved.',
        'namespace_owner': OWNERS[namespace],
        'mapping_status': 'observed descriptor name and callback store paired by normalized stack offset',
        'methods': rows}
    lua.append('  [%s] = {' % json.dumps(namespace))
    for row in rows:
        lua.append('    [%s] = %s,' % (json.dumps(row['name']), json.dumps(row['callback'])))
    lua.append('  },')
lua.append('}')
(HERE/'engine-binding-registry.json').write_text(json.dumps(report, indent=2)+'\n')
(HERE/'engine_binding_registry.lua').write_text('\n'.join(lua)+'\n')
print(json.dumps({name: value['count'] for name, value in report['namespaces'].items()}))
