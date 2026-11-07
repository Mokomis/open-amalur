from pathlib import Path
import json,hashlib,struct,platform
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';out=r/'outputs/scene-v08';rows=json.loads((out/'asset-macros.json').read_text())
for row in rows:
 p=out/'assets'/row['file'];b=p.read_bytes();version,count=struct.unpack_from('<II',b);assert version==1 and len(b)==8+count*8;row['entries']=count;row['bytes']=len(b);row['sha256']=hashlib.sha256(b).hexdigest();row['thunk_low_word']=(row['category']<<4)|11
j={'source_sha256':'16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314','macros':rows,'scope':'Explicit preview catalog selections. Category and basename associations traced in original executable. Generic host maps only hash/name to canonical typed IDs. Native asset loading/mount precedence not reproduced. FAB and SIMSPACE explicitly select patch catalogs; DIALOG_TOPIC and GLOBALOBJECTREF select base catalogs. Conflicting variants remain excluded; see selection reports.'};(out/'asset-catalog-summary.json').write_text(json.dumps(j,indent=2));print(json.dumps([{'name':x['name'],'entries':x['entries']} for x in rows]))
