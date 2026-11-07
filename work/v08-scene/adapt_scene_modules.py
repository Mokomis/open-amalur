from pathlib import Path
import platform,json,hashlib,sys
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';sys.path.insert(0,str(r/'work/v08-scripts'))
from module_source_adapter import adapt_source
out=r/'outputs/scene-v08/modules';inventory=out/'module-inventory.json';j=json.loads(inventory.read_text(encoding='utf-8-sig'));records=[]
def sha(b):return hashlib.sha256(b).hexdigest()
prepared=[]
for m in j['modules']:
 p=out/m['source_file'];original=(out/'original'/m['source_file']).read_bytes();assert sha(original)==m['frozen_source_sha256']
 s,report=adapt_source(original.decode('utf-8-sig'));data=s.encode('utf8');records.append({'module':m['module'],'original_sha256':sha(original),'output_sha256':sha(data),**report});prepared.append((p,data,m,report))
assert len(prepared)==j['registered_modules'] and 1<=len(prepared)<=256
for p,data,m,report in prepared:p.write_bytes(data);m['adapted_source_sha256']=sha(data);m['source_bytes']=len(data);m['admission']=report
j['total_source_bytes']=sum(len(data) for p,data,m,report in prepared)
j['source_adapter_sha256']=sha((r/'work/v08-scripts/module_source_adapter.py').read_bytes());inventory.write_text(json.dumps(j,indent=2))
report={'modules':len(records),'canonical_type11_nil_equality_guards':sum(x.get('canonical_type11_nil_equality_guards_adapted',0) for x in records),'canonical_key_guards':sum(x['canonical_type11_key_guards_adapted'] for x in records),'self_guards_preserved':sum(x['self_key_guards_preserved'] for x in records),'proxy_read_guards':sum(x.get('proxy_read_field_guards_adapted',0)+x.get('proxy_read_table_guards_adapted',0) for x in records),'write_table_guards_preserved':sum(x.get('write_table_guards_preserved',0) for x in records),'self_table_guards_preserved':sum(x.get('self_table_guards_preserved',0) for x in records),'adapter_sha256':j['source_adapter_sha256'],'records':records}
(out/'handle-key-adaptation.json').write_text(json.dumps(report,indent=2));(out/'runtime-adaptation.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='records'}))
