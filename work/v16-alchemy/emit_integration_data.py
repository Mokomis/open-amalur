"""Emit parent-owned backend data include from verified Windows audit outputs.

By default, formula definitions stay excluded until a separate verified formula
export exists. This never assigns ingredients/output values from symbolic names.
"""
from pathlib import Path
import argparse, hashlib, json, platform
assert platform.system() == 'Windows', 'All artifact processing runs on Windows'
r = Path.home() / 'Documents/Opem Amalur'
out = r / 'outputs/scene-v16-alchemy'
ap = argparse.ArgumentParser()
ap.add_argument('--verified-formulas', type=Path)
args = ap.parse_args()
catalog_path = out / 'alchemy-catalog.json'
catalog = json.loads(catalog_path.read_text(encoding='utf-8-sig'))
scenario = next(x for x in catalog['scenarios'] if x['name'] == 'no_optional_packages')
tables = scenario['tables']
reagents = sorted(tables['m_FULL_REAGENT_LIST'].items())
formulas = []
verification = None
if args.verified_formulas:
    verification = json.loads(args.verified_formulas.read_text(encoding='utf-8-sig'))
    assert verification['schema_verified'] is True
    assert verification['native_executable_sha256'] == '16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
    formulas = verification['formulas']
ids = set(tables['m_FULL_RECIPE_LIST'])
formulas = [x for x in formulas if x['id'] in ids]
seen = set()
for row in formulas:
    assert row['id'] in ids and row['id'] not in seen
    seen.add(row['id'])
    assert row['product'] > 1 and isinstance(row['difficulty'], int) and row['difficulty'] >= 0
    assert 1 <= len(row['needs']) <= 16
    assert all(isinstance(n['essence'], str) and n['essence'] and isinstance(n['quantity'], int) and n['quantity'] > 0 for n in row['needs'])
max_needs = max([4] + [len(x['needs']) for x in formulas])
quoted = lambda x: json.dumps(x, ensure_ascii=True)
lines = [
    '/* Generated from user-owned native game assets. No inventory grants. */',
    '#ifndef OA_INTEGRATION_DATA_INC', '#define OA_INTEGRATION_DATA_INC',
    '#include <stdint.h>',
    '#define OA_MAX_FORMULA_NEEDS '+str(max_needs)+'u',
    'typedef struct { uint32_t id; const char *symbol, *essence; } oa_reagent_def;',
    'typedef struct { const char *essence; unsigned quantity; } oa_ingredient_need;',
    'typedef struct { uint32_t id, product; const char *symbol; unsigned difficulty; unsigned need_count; oa_ingredient_need needs[OA_MAX_FORMULA_NEEDS]; } oa_formula_def;',
    'typedef struct { uint32_t id; const char *symbol; } oa_formula_catalog_def;',
    'static const oa_reagent_def oa_reagents[] = {']
for symbol, row in reagents:
    lines.append('  {'+str(row['sim_type'])+'u,'+quoted(symbol)+','+quoted(row['essence'])+'},')
lines += ['};', '#define OA_REAGENT_COUNT '+str(len(reagents))+'u', 'static const oa_formula_def oa_formulas[] = {']
for row in formulas:
    needs = ','.join('{'+quoted(n['essence'])+','+str(n['quantity'])+'u}' for n in row['needs'])
    lines.append('  {'+str(row['id'])+'u,'+str(row['product'])+'u,'+quoted(row['symbol'])+','+str(row['difficulty'])+'u,'+str(len(row['needs']))+'u,{'+needs+'}},')
if not formulas: lines.append('  {0u,0u,0,0u,0u,{{0,0u}}} /* sentinel; OA_FORMULA_COUNT is zero */')
lines += ['};', '#define OA_FORMULA_COUNT '+str(len(formulas))+'u', 'static const oa_formula_catalog_def oa_formula_catalog[] = {']
for key in tables['m_FULL_RECIPE_LIST']:
    lines.append('  {'+str(key)+'u,'+quoted(catalog['simtype_names'][str(key)])+'},')
lines += ['};', '#define OA_FORMULA_CATALOG_COUNT '+str(len(ids))+'u',
    'static const char oa_catalog_input_sha256[] = '+quoted(catalog['source_input_sha256'])+';',
    'static const char oa_catalog_content_profile[] = "no_optional_packages";',
    '#endif', '']
include = out / 'integration_data.inc'
include.write_text('\n'.join(lines), encoding='utf-8')
excluded = [dict(id=key, symbol=catalog['simtype_names'][str(key)], reason='Formula schema or record not verified; crafting unavailable for this catalog row') for key in sorted(ids-seen)]
receipt = dict(catalog_input_sha256=catalog['source_input_sha256'], catalog_archive=catalog['source_archive'],
    simtype_snapshot_sha256=catalog['simtype_snapshot_sha256'], catalog_json_sha256=hashlib.sha256(catalog_path.read_bytes()).hexdigest(),
    include_sha256=hashlib.sha256(include.read_bytes()).hexdigest(), source_content_profile='no_optional_packages',
    optional_entitlement_claim=False, actual_player_inventory_imported=False, production_grants=False,
    reagent_rows=len(reagents), verified_formula_rows=len(formulas), formula_catalog_rows=len(ids), excluded_formula_rows=excluded,
    formula_verification_source=str(args.verified_formulas) if args.verified_formulas else None,
    formula_verification_sha256=hashlib.sha256(args.verified_formulas.read_bytes()).hexdigest() if args.verified_formulas else None)
(out / 'integration-data-receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(dict(reagents=len(reagents), verified_formulas=len(formulas), excluded_formulas=len(excluded), include_sha256=receipt['include_sha256'])))
