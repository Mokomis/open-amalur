"""Windows-only: recover changed UI Lua and export real alchemy catalog references.

Pure catalog evaluation supplies exact native symbolic IDs, preserves SL tokens,
and explicitly chooses content-package branches for analysis. No player state is
invented and no native/player/UI service is called or successfully stubbed.
"""
from pathlib import Path
import csv, hashlib, json, platform, struct, subprocess, sys
assert platform.system() == 'Windows'
r = Path.home() / 'Documents/Opem Amalur'
sys.path[:0] = [str(r / p) for p in ['src', 'tools/python-libs', 'work/v08-scripts', 'work/v15-properties', 'work/v13-properties', 'work/v07-bxml']]
from native_type_catalog import index_batch, member_bytes, decode_type
from amalur_script import parse_file
from amalur_reconstruct import reconstruct
from module_source_adapter import adapt_source
from amalur_native_enums import extract_native
from amalur_enums import snapshot as enum_snapshot
from lupa.lua51 import LuaRuntime, lua_type
out = r / 'outputs/scene-v16-alchemy'
out.mkdir(exist_ok=True)
profile = json.loads((r / 'outputs/native-script-profile.json').read_text())
data = (r / 'work/scene-inputs-v09/patch_0.pak/134230570_klua.batch').read_bytes()
idx = index_batch(data)
raw = member_bytes(data, idx['members'][150180])
digest = hashlib.sha256(raw).hexdigest()
assert digest == 'a486dea8ed2ac7d100a4c12a5d20771c1b540586c0dfb846a98e902702ac39b2'
draft = out / 'patch-alchemy-win' / digest
draft.mkdir(parents=True, exist_ok=True)
input_path = draft / '150180.lua_bxml'
input_path.write_bytes(raw)
ir, source = reconstruct(parse_file(input_path), profile)
(draft / 'whole-script.lua').write_text(source, encoding='utf-8')
(draft / 'ir.json').write_text(json.dumps(ir, separators=(',', ':')), encoding='utf-8')
lua = LuaRuntime(register_eval=False, register_builtins=False, unpack_returned_tuples=True)
compiled, error = lua.eval('function(s) local f,e=loadstring(s);return f~=nil,e end')(source)
assert compiled, error

symbol_dir = r / 'references/ZucchiniZap--AmalurBxmlConverter/bin/Release/net10.0-windows/symbol_tables'
symbol_rows = list(csv.DictReader((symbol_dir / 'simtype.csv').open(encoding='utf-8-sig')))
by_name = {x['value']: int(x['id']) for x in symbol_rows}
by_id = {int(x['id']): x['value'] for x in symbol_rows}
snapshot_path = r / 'outputs/scene-v08/assets/simtype_init.bin'
snapshot = snapshot_path.read_bytes()
snapshot_digest = hashlib.sha256(snapshot).hexdigest()
assert snapshot_digest == 'fbd51309e81816a152f8bfffcdd1440df5864d0a5e263373ac40db63c92a6fd8'
version, count = struct.unpack_from('<II', snapshot)
assert version == 1 and len(snapshot) == 8 + count * 8
ids = struct.unpack_from('<'+str(count)+'I', snapshot, 8)
hashes = struct.unpack_from('<'+str(count)+'I', snapshot, 8+count*4)
assert len(set(hashes)) == count
id_by_hash = dict(zip(hashes, ids))
hash_table = json.loads((r / 'outputs/bytecode-reader/v07-hash-table.json').read_text())
weights = struct.unpack('<50I', bytes.fromhex(hash_table['ranges'][0]['raw_hex']))
used_symbols = {}
def name_hash(name):
    encoded = name.encode('ascii').lower()
    return sum(weights[i%50]*v + weights[v%50]*(i+1) for i,v in enumerate(encoded)) & 0xffffffff
def resolve_simtype(name):
    hashed = name_hash(name)
    native_id = id_by_hash.get(hashed)
    if native_id is None: raise ValueError('Name absent from selected native SimType snapshot: '+name)
    used_symbols[native_id] = name
    return native_id
enum_bytes = (r / 'outputs/scene-v08/assets/compiled_enums.bin').read_bytes()
native_enums = extract_native(Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe').read_bytes())
rebuilt_enum_bytes, enum_receipt = enum_snapshot(native_enums)
assert enum_bytes == rebuilt_enum_bytes, 'Selected enum snapshot differs from pinned native executable descriptor table'
assert enum_bytes[:4] == b'AENU' and struct.unpack_from('<I', enum_bytes, 4)[0] == 1
enum_count = struct.unpack_from('<I', enum_bytes, 8)[0]
assert len(enum_bytes) == 12+enum_count*12
enum_by_hash = {(g,m):v for g,m,v in struct.iter_unpack('<IIi',enum_bytes[12:])}
def resolve_enum(group, member):
    return enum_by_hash[(name_hash(group), name_hash(member))]
base_index = json.loads((out / 'source-audit/source-index.json').read_text())
recipe_row = next(x for x in base_index if x['name'] == 'AlchemyRecipes')
recipe_raw = member_bytes(data, idx['members'][505459])
recipe_digest = hashlib.sha256(recipe_raw).hexdigest()
assert recipe_digest == 'd2d8edec5856caadcfc5a4fbda8ec4a0868848eb0f196ad9473ece29ba30f699'
recipe_dir = out / 'patch-alchemy-recipes' / recipe_digest
recipe_dir.mkdir(parents=True, exist_ok=True)
recipe_input_path = recipe_dir / '505459.lua_bxml'
recipe_input_path.write_bytes(recipe_raw)
recipe_ir, recipe_source = reconstruct(parse_file(recipe_input_path), profile)
source_path = recipe_dir / 'whole-script.lua'
source_path.write_text(recipe_source, encoding='utf-8')
(recipe_dir / 'ir.json').write_text(json.dumps(recipe_ir, separators=(',', ':')), encoding='utf-8')
assert recipe_ir['summary']['unresolved_function_bodies'] == 0
adapted, admission = adapt_source(source_path.read_text(encoding='utf-8-sig'))

def convert(value):
    if lua_type(value) == 'table':
        pairs = list(value.items())
        if pairs and all(isinstance(k, (int, float)) and k == int(k) and k >= 1 for k, v in pairs):
            keys = {int(k) for k, v in pairs}
            if keys == set(range(1, len(pairs) + 1)):
                return [convert(value[i]) for i in range(1, len(pairs) + 1)]
        return {str(k): convert(v) for k, v in pairs}
    return value

scenarios = []
for name, active in [('no_optional_packages', False)]:
    l = LuaRuntime(register_eval=False, register_builtins=False, unpack_returned_tuples=True)
    l.globals().resolve_simtype_name = resolve_simtype
    l.globals().resolve_enum_name = resolve_enum
    l.globals().analysis_content_active = active
    l.execute('''
      function SIMTYPE_ID(name) return resolve_simtype_name(name) end
      function SL(token) return token end
      function STE(tableName, entry) return resolve_enum_name(tableName, entry) end
      GAME={is_content_package_active=function(id) return analysis_content_active end}
      function __amalur_module_table_allowed(t)
        local m=getmetatable(t); return type(t)=='table' and type(m)=='table' and m.__index==_G
      end
    ''')
    l.execute(adapted)
    module = l.globals().AlchemyRecipes
    tables = {key: convert(module[key]) for key in ['m_FULL_REAGENT_LIST', 'm_ordered_reagent_list_by_simtype', 'm_ordered_reagent_list', 'm_REAGENTS_BY_ESSENCE', 'm_REAGENT_DATA_BY_ESSENCE', 'm_REAGENT_NAME_BY_ESSENCE', 'm_FULL_RECIPE_LIST']}
    scenarios.append(dict(name=name, entitlement_claim=False, tables=tables))
catalog = dict(source_input_sha256=recipe_digest, source_resource_id=505459,
    source_archive='patch_0.pak', initial_source_input_sha256=recipe_row['sha256'], archive_precedence_claim=False,
    simtype_snapshot_sha256=snapshot_digest,
    enum_snapshot_sha256=hashlib.sha256(enum_bytes).hexdigest(), enum_snapshot_equals_pinned_native=True,
    enum_groups={g['name']:{m['name']:m['value_int32'] for m in g['members']} for g in native_enums['groups']},
    scope='Real Lua catalog declarations; SL values retained as unresolved localization tokens. Recipe ingredient/output schema is NOT defined by this list.',
    native_symbol_ids=True, actual_player_inventory_imported=False,
    scenarios=scenarios, simtype_names={str(k): v for k,v in used_symbols.items()})
(out / 'alchemy-catalog.json').write_text(json.dumps(catalog, indent=2), encoding='utf-8')

type_index = json.loads((r / 'outputs/scene-v15/native-type-index.json').read_text())
meta = {x['type_id']: x for x in type_index['types']}
components = json.loads((r / 'outputs/scene-v13/component-map.json').read_text())['components']
names = {p['kind']: p['tables'][0]['name'] for p in components}
type_data = (r / 'work/scene-inputs-v09/patch_0.pak/134225858_ksmt.batch').read_bytes()
type_batch = index_batch(type_data)
pending = set(int(k) for k in catalog['simtype_names'])
selected = []
seen = set()
while pending:
    key = pending.pop()
    if key in seen or key in (0, 1, 0xffffffff): continue
    seen.add(key)
    if key not in type_batch['members']: raise ValueError('Missing native catalog type '+str(key))
    payload = member_bytes(type_data, type_batch['members'][key])
    decoded = decode_type(payload, names)
    # Complete raw bytes preserve unknown component structures and relocations.
    selected.append(dict(metadata=meta[key], decoded=decoded, raw_hex=payload.hex()))
    pending.add(decoded['parent_key_u32'])
(out / 'alchemy-native-types.json').write_text(json.dumps(selected, indent=2), encoding='utf-8')
summary = dict(patch_alchemy_win_input_sha256=digest, patch_ui_recovery=ir['summary'], patch_ui_lua51_compiles=bool(compiled),
    patch_alchemy_recipes_input_sha256=recipe_digest, patch_catalog_recovery=recipe_ir['summary'],
    catalog_scenarios=[dict(name=x['name'], reagents=len(x['tables']['m_FULL_REAGENT_LIST']), recipes=len(x['tables']['m_FULL_RECIPE_LIST'])) for x in scenarios], native_selected_types=len(selected),
    hard_gap='Native ingredient/quantity/product schema remains unknown; no crafting success claimed')
(out / 'data-export-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps(summary, indent=2))
