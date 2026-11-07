from pathlib import Path
import json,struct,hashlib,numpy as np
R=Path(r'C:\Users\rwill\Documents\Opem Amalur');O=R/'work/v49-character-create/weighted-material-integration'
def H(x):return hashlib.sha256(x).hexdigest()
base=(R/'work/v49-character-create/packs/Almain_Male/character.bin').read_bytes()
attrs=(R/'work/v49-character-create/vertex-contract-audit/almain-male-attributes.oacat').read_bytes()
pal=(R/'work/v49-character-create/limb-skinning-audit/almain-male-palette-corrections.oacpl').read_bytes()
assert H(base)=='ede399d687bcbbc9d1534a208e81a13b9b3785a6f2b52dc25b28f78f36a484a4'
assert H(attrs)=='ab02a4a4c87996f5ac5584987455e812f6286c87a563b2bbfbca4b635c7635bf'
assert H(pal)=='6ebc4821b5e2dcfbea1d5bf79fd27754820c57b3a7b73611a31acbbab242b24f'
j,nc,np_,nt=struct.unpack_from('<4I',base,8);at=24+((j+1)//2)*4
for i in range(nc):
 frames=struct.unpack_from('<I',base,at)[0];at+=8+frames*j*28
for i in range(nt):
 w,h=struct.unpack_from('<2I',base,at);at+=8+w*h*4
parts=[]
for i in range(np_):
 nv,ni,pc,tex=struct.unpack_from('<4I',base,at);at+=16
 parts.append(dict(vertices=nv,indices=ni,palette_count=pc,palette=at,vertex=at+pc*32,index=at+pc*32+nv*52))
 at+=pc*32+nv*52+ni*4
assert at==len(base)
fixed=bytearray(base);at=64
for i in range(12):
 rec=attrs[at:at+128];pi,fab,asm,mid,stride,nv,ni,flags=struct.unpack_from('<8I',rec);at+=128
 a=np.frombuffer(attrs,dtype=np.uint8,count=nv*64,offset=at).reshape(nv,64);at+=nv*64+nv*stride
 shorts=a[:,:6].copy().view('<i2').reshape(nv,3)
 normal=np.maximum(np.float32(-1),shorts.astype(np.float32)/np.float32(32767))
 for v in range(nv):fixed[parts[pi]['vertex']+v*52+12:parts[pi]['vertex']+v*52+24]=normal[v].astype('<f4').tobytes()
assert at==len(attrs)
at=64
for i in range(2):
 pi,fab,asm,count,capacity=struct.unpack_from('<5I',pal,at);at+=128
 fixed[parts[pi]['palette']:parts[pi]['palette']+count*32]=pal[at:at+count*32];at+=count*32
assert at==len(pal)
manifest_path=R/'work/v49-character-create/material-integration/native-clothing-stage/manifest.json'
m=json.loads(manifest_path.read_text());mats={x['material']:x for x in m['materials']};tex={x['asset']:x for x in m['textures']}
inc=['/* Generated only from pinned source manifests; do not hand-retune. */',f'static const char corrected_pack_sha[]="{H(fixed)}";',
     'static const Approved approved[4]={']
for a in m['parts']:
 pp=parts[a['part']];mt=mats[a['material']];params=mt['parameters']
 def fv(v):return '{'+','.join(format(float(x),'.17g')+('f' if float(x)%1 else '.0f') for x in v)+'}'
 # Avoid1.7000000476837158f versus integer formatting issues.
 profile='{'+','.join(fv(params[n]) for n in ['ConstantColor','SpecularValues','CharacterExtraTerms2','FresnelValues2'])+'}'
 textures=[]
 for slot in [0,3,2]:
  t=tex[mt['texture_source_slots'][str(slot)]]
  data=(manifest_path.parent/t['portable_file']).read_bytes();assert H(data)==t['portable_sha256']
  textures.append('{'+str(t['asset'])+'u,"'+t['portable_file']+'",'+str(len(data))+'u,"'+H(data)+'"}')
 inc.append('{'+','.join(str(a[k])+'u' for k in ['part','fab','assembly','material','stride','flags'])+','+str(pp['vertices'])+'u,'+str(pp['indices'])+'u,'+str(pp['palette_count'])+'u,'+profile+',{'+','.join(textures)+'}},')
inc+=['};']
(O/'clothing_source_tables.inc').write_text('\n'.join(inc)+'\n')
out={'original_pack_sha256':H(base),'corrected_heap_pack_sha256':H(fixed),'attributes_sha256':H(attrs),'palettes_sha256':H(pal),'source_manifest':str(manifest_path.relative_to(R)),'source_manifest_sha256':H(manifest_path.read_bytes()),'geometry_part_info':[{'part':a['part'],**parts[a['part']]} for a in m['parts']],'policy':'Generated expected repaired heap only in memory. No existing source/pack/asset changes or output pack copy.'}
(O/'source-generation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
