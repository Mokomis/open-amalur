"""Private, read-only source join. Outputs ONLY below this script's own stage directory."""
from pathlib import Path
import sys,struct,json,hashlib,math,collections
sys.dont_write_bytecode=True
ROOT=Path(r'C:\Users\rwill\Documents\Opem Amalur')
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'work/v07-mesh'))
import amalur_mesh,amalur_fab
H=lambda b:hashlib.sha256(b).hexdigest()
def dump(name,obj):(OUT/name).write_text(json.dumps(obj,indent=2),encoding='utf-8')
def source(name):
 for a in ['patch_0.pak','initial_0.pak','DATA_0.pak']:
  for d in ['work/v49-character-create/source','work/v20-inputs']:
   q=ROOT/d/a/name
   if q.exists():return q
 raise ValueError('Missing cached source '+name)
def parse_pack(b):
 assert b[:8]==b'OACHAR01'
 j,nc,np,nt=struct.unpack_from('<4I',b,8);a=24+2*j
 for _ in range(nc):
  frames,fps=struct.unpack_from('<If',b,a);a+=8+frames*j*28
 for _ in range(nt):
  w,h=struct.unpack_from('<II',b,a);a+=8+4*w*h
 parts=[]
 for i in range(np):
  v,k,p,t=struct.unpack_from('<IIIi',b,a);a+=16;palo=a;a+=p*32
  va=a;a+=v*52;ia=a;a+=k*4
  parts.append(dict(index=i,vertices=v,indices=k,palette_count=p,texture=t,palette_offset=palo,vertex_offset=va,index_offset=ia))
 assert a==len(b)
 return parts

def main():
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'evidence').mkdir(exist_ok=True);(OUT/'materials').mkdir(exist_ok=True)
 pack_path=ROOT/'work/v49-character-create/packs/Almain_Male/character.bin'
 pack=pack_path.read_bytes();parts=parse_pack(pack)
 report=json.loads(pack_path.with_name('character-report.json').read_text())
 assert H(pack)==report['sha256']
 # Exact recorded declarations, not an importer or ISGN inference.
 layouts={}
 for run in ['oa_rec-dal-original','oa_rec-standstill']:
  q=ROOT/'work/v30-engine'/run/'resources.txt';b=q.read_bytes()
  hits=[dict(line=i+1,text=l) for i,l in enumerate(b.decode().splitlines()) if 'layout ' in l and 'BONEWEIGHT' in l]
  unique=sorted({r['text'][r['text'].index('layout '):] for r in hits})
  assert len(unique)==4
  layouts[run]=dict(path=str(q.relative_to(ROOT)),sha256=H(b),lines=hits,unique=unique)
 dump('evidence/recorded-input-layouts.json',layouts)
 common=[('POSITION',0,6,0,12),('BONEINDEX',0,32,12,4),('BONEWEIGHT',0,13,16,8),('TEXCOORD',0,16,24,8)]
 profile={}
 for stride,kind,n,u,c in [(56,17,32,None,None),(60,22,32,None,56),(64,25,40,32,None),(68,27,40,32,64)]:
  # For68 type27 not witnessed among this selected candidate; do NOT assert enum.
  decl=common.copy()
  if u is not None:decl.append(('TEXCOORD',1,16,u,8))
  decl += [('NORMAL',0,13,n,8),('TANGENT',0,13,n+8,8),('BINORMAL',0,13,n+16,8)]
  if c is not None:decl.append(('COLOR',0,28,c,4))
  profile[stride]=dict(stride=stride,source_type=kind if stride!=68 else None,normal=n,uv1=u,color=c,stream0=decl,
   missing_stream1=[k for k,v in [('COLOR',c),('TEXCOORD1',u)] if v is None])
 # All appended offsets are unambiguous from recorded formats and per-slot preceding widths.
 dump('evidence/weighted-layout-correspondence.json',dict(profiles=profile,
  formats={'6':'R32G32B32_FLOAT','32':'R8G8B8A8_UINT','13':'R16G16B16A16_SNORM','16':'R32G32_FLOAT','28':'R8G8B8A8_UNORM'},
  domain='Recorded original-engine declarations + exact serialized stride/type correspondence. Not per-part executed draw identity.',
  snorm_rule='max(-1, signed16 / 32767); do not renormalize source vectors.',
  stream1='Recorded declarations provide absent COLOR/UV1 from stream1, not these sourceVB bytes. Its runtime contents are unjoined.'))
 side=bytearray(b'OACAT01\0'+struct.pack('<6I',1,len(parts),12,128,64,0)+bytes.fromhex(H(pack)))
 assert len(side)==64
 rows=[];material_ids=set();part_index=0
 for fid,label in report['source_recipe']['parts']:
  meshpath=source(str(fid)+'.fab_visual_data_streamable_bin');fabpath=source(str(fid)+'.fab_bxml')
  raw=meshpath.read_bytes();fb=fabpath.read_bytes();m=amalur_mesh.parse_bytes(raw);f=amalur_fab.parse_bytes(fb)
  assert f['mesh_count']==len(m['assemblies'])
  for ai,asm in enumerate(m['assemblies']):
   if asm['unknown_u16_at2']:continue
   d=f['mesh_descriptors'][ai];tail=bytes.fromhex(d['tail25_hex'])
   mid,shader,variant,vtype=struct.unpack_from('<4I',tail)
   if mid in (1751215,518048):continue # existing builder intentionally omits these two authored surfaces
   old=parts[part_index];pr=report['parts'][part_index]
   assert pr['fab']==fid and pr['label']==label
   vb=m['vertex_buffers'][asm['vertex_buffer']];ib=m['index_buffers'][asm['index_buffer']]
   stride=vb['stride_bytes'];pf=profile[stride];nv=vb['vertex_count'];ni=ib['index_count']
   assert stride in (56,60,64) and vtype==pf['source_type'] and asm['unknown_u32_at8'][0]==vtype
   assert (nv,ni)==(old['vertices'],old['indices'])
   vraw=raw[vb['data_file_offset']:vb['data_file_offset']+nv*stride]
   iraw=struct.pack('<'+'I'*ni,*ib['indices'])
   assert iraw==pack[old['index_offset']:old['index_offset']+4*ni]
   # Source type + material + shader are read at an exact parsed descriptor boundary, not scanned.
   matpath=source(str(mid)+'.mat_bxml');mat=matpath.read_bytes()
   param_ptr,param_count,tex_ptr,tex_count,mat_shader=struct.unpack_from('<5I',mat,8)
   assert shader==mat_shader
   assert param_ptr+24*param_count<=len(mat) and tex_ptr+8*tex_count<=len(mat)
   material_ids.add(mid)
   textures=[dict(source_slot=slot,texture_id=tex,file_offset=tex_ptr+8*k) for k,(tex,slot) in enumerate(struct.iter_unpack('<II',mat[tex_ptr:tex_ptr+8*tex_count]))]
   params=[dict(file_offset=param_ptr+24*k,value_bytes=mat[param_ptr+24*k:param_ptr+24*k+16].hex(),type=struct.unpack_from('<I',mat,param_ptr+24*k+16)[0],key=struct.unpack_from('<I',mat,param_ptr+24*k+20)[0]) for k in range(param_count)]
   dump('materials/'+str(mid)+'.json',dict(material_id=mid,path=str(matpath.relative_to(ROOT)),sha256=H(mat),shader_id=shader,source_slots=textures,parameters=params,header_bytes=mat[:40].hex(),runtime_sampler_identity='Not recovered by this source-only join'))
   (OUT/'materials'/str(mid)).with_suffix('.mat_bxml').write_bytes(mat)
   attrs=bytearray();normal_dif=0;maxerr=0.;old_offset_counts=collections.Counter();unique_uv1=0;colset=set()
   flags=1|2|4|8 # N/T/B/UV0 in source
   if pf['uv1'] is not None:flags|=16
   if pf['color'] is not None:flags|=32
   for vi in range(nv):
    sv=vraw[vi*stride:(vi+1)*stride];ov=pack[old['vertex_offset']+vi*52:old['vertex_offset']+(vi+1)*52]
    assert sv[:12]==ov[:12] and sv[24:32]==ov[24:32] and sv[12:16]==ov[32:36]
    n=pf['normal'];uvw=sv[pf['uv1']:pf['uv1']+8] if pf['uv1'] is not None else bytes(8)
    color=sv[pf['color']:pf['color']+4] if pf['color'] is not None else bytes(4)
    # Store packed source vectors INCLUDING their fourth component, exact float UV bytes,
    # source RGBA only when present; absence has a separate mask, never invented white.
    av=sv[n:n+24]+sv[24:32]+uvw+color+struct.pack('<II',flags,vi)+sv[:12]
    assert len(av)==64;attrs+=av
    nn=tuple(max(-1.,x/32767.) for x in struct.unpack_from('<3h',sv,n))
    on=struct.unpack_from('<3f',ov,12);e=max(abs(x-y) for x,y in zip(nn,on));maxerr=max(e,maxerr);normal_dif+=e>1e-6
    for no in [32,36,40,44]:
     if no+6<=stride and max(abs(x/32767-y) for x,y in zip(struct.unpack_from('<3h',sv,no),on))<1e-6:old_offset_counts[no]+=1
    if pf['uv1'] is not None: unique_uv1+=uvw!=sv[24:32]
    if pf['color'] is not None:colset.add(color.hex())
   oldverts=pack[old['vertex_offset']:old['vertex_offset']+nv*52]
   record=struct.pack('<8I',part_index,fid,ai,mid,stride,nv,ni,flags)+bytes.fromhex(H(oldverts))+bytes.fromhex(H(vraw))+bytes.fromhex(H(iraw))
   assert len(record)==128
   record_offset=len(side)
   side+=record+attrs+vraw
   rows.append(dict(sidecar_record_offset=record_offset,sidecar_attribute_offset=record_offset+128,sidecar_raw_source_offset=record_offset+128+64*nv,part=part_index,label=label,fab=fid,assembly=ai,material_id=mid,shader_id=shader,vertex_type=vtype,source_stride=stride,vertices=nv,indices=ni,flags=flags,
    source_mesh=str(meshpath.relative_to(ROOT)),source_mesh_sha256=H(raw),source_fab=str(fabpath.relative_to(ROOT)),source_fab_sha256=H(fb),
    source_vb=asm['vertex_buffer'],source_ib=asm['index_buffer'],source_vb_data_file_offset=vb['data_file_offset'],source_vb_sha256=H(vraw),
    descriptor_offset=d['file_offset'],material_file_offset=d['file_offset']+d['byte_length']-25,descriptor_tail25_hex=tail.hex(),
    old_vertex_sha256=H(oldverts),indices_sha256=H(iraw),attributes_sha256=H(attrs),
    old_normals_disagree_vertices=normal_dif,old_normal_max_component_error=maxerr,old_normal_matching_offset_vertex_counts=dict(old_offset_counts),
    authored_secondUV_different_from_UV0_vertices=unique_uv1,authored_colors=sorted(colset),missing_runtime_stream1=pf['missing_stream1']))
   part_index+=1
 assert part_index==12 and len(parts)==17
 target=OUT/'almain-male-attributes.oacat';target.write_bytes(side)
 dump('source-join-manifest.json',dict(schema=1,pack=str(pack_path.relative_to(ROOT)),pack_sha256=H(pack),pack_bytes=len(pack),base_parts=len(parts),covered_parts=part_index,
  sidecar=target.name,sidecar_bytes=len(side),sidecar_sha256=H(side),parts=rows,
  excluded_base_parts=[dict(part=i,label=report['parts'][i]['label'],reason='Existing rigid weapon attachments are outside weighted appearance scope; leave52B path unchanged') for i in range(12,17)],
  existing_policy_preserved=['52B source pack bytes','palettes','bone indices','legacy three-weight remainder and fourth-weight policy','indices/order','animations','bind matrices','part visibility'],
  proof_limits=['No current candidate native draw capture: declaration-to-specific-part join is source stride/type correspondence, not executed pipeline identity.',
   'Missing source COLOR/UV1 is runtime stream1 in native declarations; values are unknown here. Zero placeholders MUST NOT be treated as authored values.',
   'Descriptor material/shader IDs are exact source fields; runtime per-instance texture/color substitutions and sampler state are separate.',
   'Old builder omits source eye_shadow/mouth_black surfaces and approximates facial bones; sidecar does not cure those limitations.']))
 print(json.dumps(dict(parts=len(rows),vertices=sum(r['vertices'] for r in rows),bytes=len(side),normal_disagreements=sum(r['old_normals_disagree_vertices'] for r in rows),sha256=H(side))))
if __name__=='__main__':main()
