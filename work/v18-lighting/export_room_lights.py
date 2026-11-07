"""Windows-only scene light data export with qualified, explicit field provenance."""
from pathlib import Path
import hashlib,json,math,platform,struct,xml.etree.ElementTree as ET
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';o=r/'outputs/scene-v18';host=r/'work/v18-host'
source=r/'work/scene-inputs-v07/DATA_0.pak/524859.space_bxml';b=source.read_bytes();digest=hashlib.sha256(b).hexdigest();assert digest=='775fb38b3fd9ff67ed3181579e935c70b33bd6831ccebf744ce4b2f6cd590143'
ptr,count=struct.unpack_from('<II',b,8+0x90);assert count==36 and ptr+count*108<=8+struct.unpack_from('<I',b)[0]
template=r/'work/v18-inputs/initial_0.pak/int_walllamp_dok_w_light.koagrouptemplate';root=ET.parse(template).getroot();light=root.find(".//value[@type='Light::WELIGHT']");assert light.find("value[@name='type']").text=='Point'
keys=['Midnight','Dawn','Noon','Dusk'];configs=light.find("value[@name='configs']");assert [v.attrib['name']for v in configs]==keys
for config in configs:assert all(config.find("value[@name='"+field+"']")is not None for field in ['diffuse','multiplier','attenuation_start','attenuation_end'])
rows=[]
for i in range(count):
 raw=b[ptr+i*108:ptr+(i+1)*108];values=struct.unpack('<27f',raw);assert all(math.isfinite(x)for x in values)
 palettes=[list(values[3+3*j:6+3*j])+[values[15+j],values[19+j],values[23+j]]for j in range(4)];assert all(p==palettes[0]for p in palettes), 'No authored time-of-day choice permitted'
 color=palettes[0][:3];multiplier,start,end=palettes[0][3:];assert all(0<=x<=16 for x in color)and 0<=multiplier<=16 and 0<=start<end<=10000
 rows.append(dict(index=i,position=list(values[:3]),color=color,multiplier=multiplier,attenuation_start=start,attenuation_end=end,all_four_time_keys_equal=True,source_offset=ptr+i*108,source_record_sha256=hashlib.sha256(raw).hexdigest()))
canonical=json.dumps(rows,separators=(',',':'),sort_keys=True).encode();data_sha=hashlib.sha256(canonical).hexdigest()
lines=['/* Generated user-owned scene data. Renderer equation is authored. */','#define OPEM_ROOM_LIGHT_COUNT 36u','#define OPEM_ROOM_LIGHT_DATA_SHA256 "'+data_sha+'"','static const opem_room_light opem_room_lights[OPEM_ROOM_LIGHT_COUNT]={']
for row in rows:
 fmt=lambda seq:','.join(format(float(v),'.9e')+'f'for v in seq)
 lines.append('{{'+fmt(row['position'])+'},{'+fmt(row['color'])+'},'+fmt([row['multiplier'],row['attenuation_start'],row['attenuation_end']])+'},')
lines+=['};',''];include=host/'room_lights.inc';include.write_text('\n'.join(lines),encoding='utf-8')
report=dict(source_scene_sha256=digest,source_span_sha256=hashlib.sha256(b[ptr:ptr+count*108]).hexdigest(),root_slot=0x90,source_stride=108,count=count,source_pointer_count_native_evidence='Space::Load0xfdc910 copies root90/94 to wrapper8/c',field_evidence='Original shipped Light::WELIGHT / LightConfigTimeOfDay authoring schema plus exact source-record patterns and flame-position correlations. Native per-field renderer ingestion not yet traced.',schema_template=str(template),schema_template_sha256=hashlib.sha256(template.read_bytes()).hexdigest(),time_key_names=keys,time_of_day_choice_required=False,all_four_time_keys_equal=True,rows=rows,data_sha256=data_sha,include_sha256=hashlib.sha256(include.read_bytes()).hexdigest(),renderer=dict(falloff='Authored linear attenuation between source attenuation_start/end; native curve not verified',ambient=[.12,.12,.12],ambient_status='Authored fallback; actual room preset binding unresolved',post_processing='Unchanged opaque preview, no native tone mapping/bloom/color correction parity',shadow_status='No new shadow implementation; source shadow classification unresolved'),native_lighting_parity_verified=False)
(o/'room-lighting.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(lights=count,time_keys_equal=True,data_sha256=data_sha,native_lighting_parity_verified=False)))
