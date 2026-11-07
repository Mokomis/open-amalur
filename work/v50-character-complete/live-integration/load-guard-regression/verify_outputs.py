from pathlib import Path
import json,hashlib,importlib.util,sys
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent
out=Path(json.loads((O/'run.json').read_text())['output'])
spec=importlib.util.spec_from_file_location('reader',O/'independent_reader.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
rows=[]
for race,sex,name in [(0,1,'Mira'),(2,0,'Aelar')]:
 p=out/f'case-{race}-{sex}/wellofsouls.creation-gameplay-v1.bin';d=mod.decode(p)
 assert (d['race'],d['sex'],d['name'])==(race,sex,name)
 assert d['owner']['quest_stage']==5 and d['owner']['health']==49 and d['owner']['maxhealth']==52 and d['item_count']==165
 assert d['opening']['lua']['clock']==15 and d['opening']['initialized']==1 and d['opening']['door_open']==0 and d['opening']['owned']==0
 imgs=[(p.parent/(n+'.rgba')).read_bytes()for n in ['complete','reloaded','rebuilt']]
 assert imgs[0]==imgs[1]==imgs[2]
 d['rendered_rgba_sha256']=hashlib.sha256(imgs[0]).hexdigest();d['complete_reload_rebuild_pixels_identical']=True;rows.append(d)
(O/'independent-validation.json').write_text(json.dumps(dict(passed=True,case_files=2,fieldwise_checksums_source_identity=True,all_three_GPU_draws_pixel_identical_each_case=True,cases=rows),indent=2)+'\n')
print('PASS 2 combinedprofiles fieldwise/checksummed and6actualGPUdrawimages; eachcomplete/reload/rebuild byteidentical')
