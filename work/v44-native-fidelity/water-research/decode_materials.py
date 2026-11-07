from pathlib import Path
import json,struct,hashlib
R=Path(__file__).resolve().parent;S=json.loads((R/'evidence/water-symbols.json').read_text());out=[]
fields=['TileDiffuse1Normal1','TileNormal2','TileDiffuse2','UScrollDiffuse1Normal1','VScrollDiffuse1Normal1','UScrollDiffuse2Normal2','UScrollRefraction','VScrollRefraction','WaterReflectivity','RefractionScale','FogDepth','WaterTintColor','SpecularColor','SpecularLevel','Glossiness','RefractionBias']
reference=(R/'evidence/404112.mat_bxml').read_bytes();refpp=struct.unpack_from('<I',reference,8)[0];key_names={struct.unpack_from('<I',reference,refpp+i*24+20)[0]:name for i,name in enumerate(fields)}
for f in sorted((R/'evidence').glob('*.mat_bxml')):
 b=f.read_bytes();id=int(f.stem.split('.')[0]);pp,pc,tp,tc,shader=struct.unpack_from('<5I',b,8);records=[]
 assert pp>=8 and pp+pc*24<=len(b) and tp+tc*8<=len(b)
 for i in range(pc):
  off=pp+i*24;v=struct.unpack_from('<4f',b,off);ty,key=struct.unpack_from('<II',b,off+16);records.append(dict(offset=off,values=v,type=ty,key=key))
 tex=[dict(id=tid,slot=slot,name=S['texture'].get(str(tid))) for tid,slot in struct.iter_unpack('<II',b[tp:tp+tc*8])]
 d=dict(id=id,name=S['material'].get(str(id),'for_pond' if id==618399 else str(id)),shader=shader,shader_name=S['shader'][str(shader)],source='work/v20-inputs/initial_0.pak/'+f.name,sha256=hashlib.sha256(b).hexdigest(),parameters=records,textures=tex)
 if d['shader_name'] in ['river','rivernopointlights']:
  vals={key_names[r['key']]:(r['values'] if key_names[r['key']].endswith('Color') else r['values'][0]) for r in records if r['key'] in key_names};native=[0.0]*24
  native[11]=1.0 # capture padding, ignored by named HLSL fields
  for i in range(11):native[i]=vals[fields[i]]
  native[12:16]=vals['WaterTintColor'];native[16:20]=vals.get('SpecularColor',[0,0,0,0]);native[20]=vals['SpecularLevel'];native[21]=vals['Glossiness'];native[22]=vals['RefractionBias']
  d['river_fields']=vals;d['native_float24']=native;d['field_mapping_evidence']='key mappings recovered from riverwater ordered values and independently exact active draw material bytes; missing riverpond SpecularColor remains zero as active capture'
  (R/'resources'/f'material-{id}-native96.bin').write_bytes(struct.pack('<24f',*native))

 out.append(d)
(R/'decoded-materials.json').write_text(json.dumps(out,indent=2));print([(d['id'],d['name'],d.get('river_fields')) for d in out])
