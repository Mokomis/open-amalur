from pathlib import Path
import json,struct
r=Path.home()/'Documents/Opem Amalur';s=(r/'work/v09-scene/render_rtti.py').read_text();exec(s[:s.index('\nimport re')])
e=json.loads((r/'outputs/scene-v10/rea-session-live/mesh_vertex_declarations.json').read_text())['structuredContent'];code=e['normalized_result']
# Exact seven constants assigned to local_180..168 and passed as count7 to
# createVertexFormat, then stored in renderer slot0x65 by native c658f0.
words=[0x200,0x107,0x108,0x701,0x702,0x703,0x904];rows=[];offset=0
sizes={1:8,2:12,7:8,9:4};names={1:'float32x2',2:'float32x3',7:'snorm16x4',9:'unorm8x4'}
for word in words:
 semantic,fmt,slot,step=struct.pack('<I',word);ptr,index=struct.unpack('<II',raw(0x1972d88+semantic*8,8));name=raw(ptr,48).split(b'\0')[0].decode('ascii');rows.append(dict(semantic=name,semantic_index=index,format=names[fmt],format_enum=fmt,slot=slot,instance_step=step,byte_offset=offset,bytes=sizes[fmt]));offset+=sizes[fmt]
report=dict(evidence_id=e['evidence_id'],source_function='0xc658f0',renderer_format_slot='0x65',attribute_rows=rows,stride=offset,scope='Native vertex declaration. Selected stream header/layout association additionally uses stride56 and measured finite data; original shader behavior remains separate.')
(r/'outputs/scene-v10/native-layout56.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
