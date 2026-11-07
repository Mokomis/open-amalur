"""Windows-only frozen Workbench adaptation and scene placement manifest."""
from pathlib import Path
import hashlib,json,platform,sys
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur'
sys.path.insert(0,str(r/'work/v08-scripts'))
from module_source_adapter import adapt_source
o=r/'outputs/scene-v16';o.mkdir(exist_ok=True)
contract=json.loads((r/'outputs/scene-v15/workbench-interaction-contract.json').read_text())
src=Path(contract['original_recovered_callback']['source'])
raw=src.read_bytes()
assert hashlib.sha256(raw).hexdigest()==contract['original_recovered_callback']['recovered_source_sha256']
adapted,receipt=adapt_source(raw.decode('utf-8-sig'))
p=o/'Workbench.lua';p.write_text(adapted,encoding='utf-8',newline='\n')
scene=json.loads((r/'outputs/scene-v15/scene-native-interactions.json').read_text())
row=next(x for x in scene['objects'] if x['type_id']==230417)
assert row['native_script_id']==237033 and row['instance_id']==524875
receipt.update(source=contract['original_recovered_callback'],adapted_source_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),placement=row,scope='Original Workbench callback with existing verified table-domain adapter; authored Android UI service at alchemy_win boundary')
(o/'workbench-integration.json').write_text(json.dumps(receipt,indent=2))
pos=','.join(format(float(x),'.17g')+'f' for x in row['position_xyz'])
inc=r/'work/v16-host/workbench_placement.inc'
inc.write_text('/* Exact recovered source placement, independent of handle generation. */\nstatic const float oa_workbench_position[3]={'+pos+'};\n#define OA_WORKBENCH_SOURCE '+str(row['instance_id'])+'u\n#define OA_WORKBENCH_TYPE 230417u\n#define OA_WORKBENCH_SCRIPT 237033u\n')
print(json.dumps(dict(workbench_source_sha256=receipt['adapted_source_sha256'],source_id=row['instance_id'],position=row['position_xyz'])))
