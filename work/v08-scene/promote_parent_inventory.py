from pathlib import Path
import json,platform
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';out=r/'outputs/scene-v08';old=out/'modules';new=out/'modules-parent-candidate';a=json.loads((old/'module-inventory.json').read_text());b=json.loads((new/'module-inventory.json').read_text());aa={x['module']:x for x in a['modules']};bb={x['module']:x for x in b['modules']}
assert set(aa)<=set(bb)
for name,x in aa.items():assert x['input_sha256']==bb[name]['input_sha256'] and x['frozen_source_sha256']==bb[name]['frozen_source_sha256'],name
assert not b['missing'];assert b['required_bootstrap_module']=='ParentUtils'
report={'old_count':len(aa),'new_count':len(bb),'added_modules':sorted(set(bb)-set(aa)),'old_identities_preserved':True,'ambiguous_unselected':b['ambiguous'],'scope':'Only explicit source inventory extended; no ambiguous module selected or substituted'}
old.rename(out/'modules-before-parent');new.rename(old);(out/'parent-inventory-extension.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='ambiguous_unselected'},indent=2))
