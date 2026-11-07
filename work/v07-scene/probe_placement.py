from pathlib import Path
import struct,json
root=Path.home()/'Documents'/'Opem Amalur';raw=(root/'work/scene-inputs-v07/DATA_0.pak/524859.space_bxml').read_bytes();p=raw[8:];target,count=struct.unpack_from('<II',p,152)
rows=[]
for i in range(3):
 o=target-8+i*80
 rows.append({'index':i,'payload_offset':o,'words':[{'offset':j,'uint':struct.unpack_from('<I',p,o+j)[0],'float':struct.unpack_from('<f',p,o+j)[0]} for j in range(0,80,4)]})
report={'raw_pointer':target,'count':count,'records':rows}
(root/'outputs/scene-v07/placement-native-probe.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
