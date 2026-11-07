"""Index remaining runtime integration obligations from generated IR on Windows."""
from pathlib import Path
import json,collections,platform
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur';full=root/'outputs/initial-corpus-drafts-v05'
manifest=json.loads((full/'manifest.json').read_text());globals=collections.Counter();writes=collections.Counter();fields=collections.Counter();features=collections.Counter();records=[]
def visit(f):
 yield f
 for c in f['children']:yield from visit(c)
for h,r in manifest['unique_scripts'].items():
 ir=json.loads((full/r['directory']/'ir.json').read_text())
 for f in visit(ir['root_function']):
  kinds={x.get('kind') for x in f['instructions'] if x.get('reachable') is not False}
  obligations=[]
  if f.get('requires_uint64_adapter'):obligations.append('type11 adapter and engine marshaling')
  if kinds & {'call_fixed','call_cached_fixed','tailcall','tailcall_cached','tforloop'}:obligations.append('callee or iterator implementation')
  if kinds & {'getfield_k','getfield_cached_k','gettable','settable','setfield','setfield_cached','self','length'}:obligations.append('admitted table/string object domain')
  if kinds & {'eq_branch','lt_branch','le_branch'}:obligations.append('primitive comparison domain')
  if any(k and k.startswith('integer_') for k in kinds):obligations.append('signed-int32 numeric domain')
  if f['upvalue_count']:obligations.append('shared capture-cell environment')
  features.update(obligations)
  if obligations:records.append({'script_sha256':h,'function':f['path'],'obligations':obligations})
  for row in f['instructions']:
   if row.get('reachable') is False:continue
   k=row.get('kind');literal=row.get('constant_lua')
   if k=='getglobal':globals[literal]+=1
   elif k=='setglobal':writes[literal]+=1
   elif k in ('getfield_k','getfield_cached_k'):fields[literal]+=1
out=root/'outputs/runtime-obligations-v05.json'
report={'scope':'Exact static accesses and guarded runtime-domain dependencies across distinct wrapped script variants; counts do not identify native callees or prove dynamic execution.',
 'distinct_script_variants':len(manifest['unique_scripts']),'function_bodies':manifest['unique_totals']['functions'],
 'function_obligation_counts':dict(features),'global_read_names':len(globals),'global_write_names':len(writes),'field_read_keys':len(fields),
 'global_reads':globals.most_common(),'global_writes':writes.most_common(),'field_reads':fields.most_common(),'functions':records}
out.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ('global_reads','global_writes','field_reads','functions')},indent=2))
