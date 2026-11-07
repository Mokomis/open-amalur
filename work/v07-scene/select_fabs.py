from pathlib import Path
import json,shutil
root=Path.home()/'Documents'/'Opem Amalur';rows=json.loads((root/'outputs/scene-v07/meshes/manifest.json').read_text())['records'];out=root/'work/scene-fabs-selected-v07';out.mkdir(exist_ok=True)
for r in rows:
 p=root/Path(r['selected_input'].replace('.fab_visual_data_streamable_bin','.fab_bxml'));assert p.exists();shutil.copy2(p,out/p.name)
print('Selected',len(rows),'matching FAB variants')
