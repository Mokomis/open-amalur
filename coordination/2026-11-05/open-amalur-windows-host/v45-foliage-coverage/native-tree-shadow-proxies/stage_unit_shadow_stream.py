"""Stage caster-only full fallback plus source-authored UNIT343974 proxies; no live writes."""
from pathlib import Path
import json,struct,hashlib,collections,sys
import numpy as np
sys.dont_write_bytecode=True
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent;A=P/'work/v45-foliage-coverage';W=P/'work/v40-windows-host/assets/world';O=Q/'candidate-shadow-world-unit';O.mkdir(exist_ok=True)
sys.path.insert(0,str(P/'work/v07-mesh'));import amalur_mesh
DT=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')]);assert DT.itemsize==76
def sha(b):return hashlib.sha256(b).hexdigest()
def qr(q,v):
 u=np.array(q[:3]);x=2*np.cross(u,v);return v+q[3]*x+np.cross(u,x)
inventory=json.loads((Q/'inventory.json').read_text());allproxies=inventory['poses'];unit=[p for p in allproxies if p['scale']==[1,1,1]];assert len(unit)==34
metadata=inventory['selected_fab_classifier'];scene_asms={e for g in metadata['groups_containing_proxy'] for e in g['elements']} # reset below: scene groups are independent evidence
fabmetadata=next(m for m in json.loads((A/'instance-audit/authored-fab-groups.json').read_text()) if m['fab']==343974)
scene_asms={e for g in fabmetadata['groups'] if 1<=g['group']<=4 for e in g['element_indices']};proxy_asms={e['element'] for e in metadata['proxy_elements']};assert proxy_asms=={9} and 9 not in scene_asms
def fullkey(p):return (tuple(p['translation']),tuple(p['quaternion']),tuple(p['scale']))
def anchorkey(p):return (tuple(p['translation']),tuple(p['scale']))
unitfull={fullkey(p):p for p in unit};anchor_candidates=collections.defaultdict(list)
for p in allproxies:anchor_candidates[anchorkey(p)].append(p)
unitanchor={anchorkey(p):p for p in unit};assert len(unitfull)==34 and len(unitanchor)==34
leafsources=json.loads((A/'expanded-leaf-attributes/source-provenance.json').read_text());oldownership=json.loads((A/'native-leaf-direct-trs/manifest.json').read_text());ownership={f['file']:f for f in oldownership['files']};source_owner=np.concatenate([np.full(s['triangles'],i,int) for i,s in enumerate(leafsources)]);assert len(source_owner)==51831
removed_sources={};space_matches=[]
for i,s in enumerate(leafsources):
 if s['fab']!=343974:continue
 rr=bytes.fromhex(s['render_record_hex']);p=dict(translation=list(struct.unpack_from('<3f',rr,16)),quaternion=list(struct.unpack_from('<4f',rr,32)),scale=list(struct.unpack_from('<3f',rr,48)))
 proxy=unitfull.get(fullkey(p))
 if proxy is None:continue
 assert s['assembly'] in scene_asms and s['assembly'] not in proxy_asms and 'SPACE' in proxy['source_producers']
 removed_sources[i]=proxy;space_matches.append(dict(leaf_source_instance=i,proxy_source_index=proxy['source_index'],fab=s['fab'],assembly=s['assembly'],triangles=s['triangles'],rawTQS=p,join='exactFAB/rawTQS; visibleassemblygroup1..4, uniqueexplicitproxy9'))
assert len(removed_sources)==18 and sum(leafsources[i]['triangles'] for i in removed_sources)==1325
cells={};inputs=[];fallback_proof=[];dependencies=collections.defaultdict(set);removed_occurrences=collections.Counter();fallback_triangle_total=0
li=(W/'leaf-index.bin').read_bytes();assert li[:8]==b'OALF001\0';nc,nmaps,mc=struct.unpack_from('<3I',li,8);assert nc==175 and mc==300
for row in range(nc):
 cx,cy,ntri=struct.unpack_from('<iiI',li,20+8*nmaps+12*row);fn=f'l{cx}_{cy}.bin';b=(W/fn).read_bytes();magic,nv,ni,nd=struct.unpack_from('<4s3I',b);assert magic==b'OAWE' and ni//3==ntri
 at=16+12*nd;verts=b[at:at+76*nv];ix=np.frombuffer(b,'<u4',ni,at+76*nv).reshape(-1,3);ot=ownership[fn]['source_triangles'];assert len(ot)==len(ix)
 # Current geometry/index topology must match the proven-only frozen pack.
 frozen=(A/'native-leaf-direct-trs/proven-world'/fn).read_bytes();assert b==frozen,(fn,'currentleafchanged sinceproven staging')
 ids=source_owner[np.array(ot)];materials=np.empty(len(ix),'<u4')
 for j in range(nd):
  mat,first,count=struct.unpack_from('<3I',b,16+12*j);materials[first//3:(first+count)//3]=mat
 keep=np.array([int(i) not in removed_sources for i in ids]);newix=ix[keep].ravel().astype('<u4');ranges=[];first=0;run_start=0;kept_ids=ids[keep];kept_mats=materials[keep]
 while run_start<len(kept_ids):
  end=run_start+1
  while end<len(kept_ids) and kept_ids[end]==kept_ids[run_start] and kept_mats[end]==kept_mats[run_start]:end+=1
  owner=int(kept_ids[run_start]);rr=bytes.fromhex(leafsources[owner]['render_record_hex']);t=struct.unpack_from('<3f',rr,16);sphere=struct.unpack_from('<4f',rr);count=(end-run_start)*3
  ranges.append(struct.pack('<4I6fIf',int(kept_mats[run_start]),first,count,0,*t,sphere[3],0,np.finfo(np.float32).max,owner,1.0));first+=count;run_start=end
 for owner in ids[~keep]:
  proxy=removed_sources[int(owner)];anchor=tuple(np.floor(np.array(proxy['translation'][:2])/6400).astype(int));dependencies[(cx,cy)].add(anchor);removed_occurrences[int(owner)]+=1
 assert np.array_equal(newix.reshape(-1,3),ix[keep]);assert verts==frozen[at:at+76*nv]
 cells[(cx,cy)]=dict(vertices=[verts],indices=[newix.tobytes()],ranges=ranges,nv=nv,ni=len(newix),fallback_vertices=nv,fallback_triangles=int(keep.sum()),proxy_sources=[])
 inputs.append(dict(file=fn,sha256=sha(b),triangles=ntri,vertices=nv));fallback_triangle_total+=int(keep.sum())
 fallback_proof.append(dict(cell=[cx,cy],retained_triangles=int(keep.sum()),removed_triangles=int((~keep).sum()),full_vertex_payload_byteexact=True,retained_index_triangles_byteexact_and_ordered=True,removed_source_counts=dict(collections.Counter(int(i) for i in ids[~keep]))))
assert fallback_triangle_total==50506 and sum(removed_occurrences.values())==1325
assert all(removed_occurrences[i]==leafsources[i]['triangles'] for i in removed_sources)
meshfile=next(P/'work/v20-inputs'/pack/'343974.fab_visual_data_streamable_bin' for pack in ['patch_0.pak','initial_0.pak','DATA_0.pak'] if (P/'work/v20-inputs'/pack/'343974.fab_visual_data_streamable_bin').exists());mesh=amalur_mesh.parse_file(meshfile);src=meshfile.read_bytes();asm=mesh['assemblies'][9];vb=mesh['vertex_buffers'][asm['vertex_buffer']];stride=vb['stride_bytes'];base=vb['data_file_offset'];nv=vb['vertex_count'];assert stride==48 and nv==28
local=np.ndarray((nv,3),'<f4',src,base,(stride,4));uv=np.ndarray((nv,2),'<f4',src,base+12,(stride,4));localN=np.maximum(np.ndarray((nv,3),'<i2',src,base+20,(stride,2)).astype(float)/32767,-1);localN/=np.maximum(np.linalg.norm(localN,axis=1,keepdims=True),1e-12);rgba=np.ndarray((nv,4),'u1',src,base+44,(stride,1));ix=np.array(mesh['index_buffers'][asm['index_buffer']]['indices'],'<u4');assert len(ix)==42
absP=np.abs(local.copy());phase=np.float32(np.float32(absP[:,0]+absP[:,1])+absP[:,2])*np.float32(.1);phase=np.float32(phase-np.floor(phase));phase=np.floor(np.float32(phase*np.float32(10))).astype('<f4');assert np.all((phase>=0)&(phase<10))
proxy_proof=[]
for p in unit:
 q=p['quaternion'];cq=(-q[0],-q[1],-q[2],q[3]);scale=np.array(p['scale']);t=np.array(p['translation']);world=qr(cq,local.astype(float)*scale)+t;wind=qr(cq,localN*scale).astype('<f4');data=np.zeros(nv,DT);data['v'][:,:3]=world;data['v'][:,3:6]=wind;data['v'][:,12:14]=uv;data['v'][:,14]=phase;data['rgba']=rgba;data['material']=1744210
 assert np.array_equal(data['v'][:,3:6].view('<u4'),wind.view('<u4')) and np.array_equal(data['v'][:,12:14].view('<u4'),uv.copy().view('<u4')) and not data['v'][:,6:12].any()
 anchor=tuple(int(x) for x in np.floor(t[:2]/6400));cell=cells.setdefault(anchor,dict(vertices=[],indices=[],ranges=[],nv=0,ni=0,fallback_vertices=0,fallback_triangles=0,proxy_sources=[]));source_id=0x20000000+p['source_index'];lohi=p['merged_intervals_squared'];assert len(lohi)==1
 # Runtime registry scale is1. Individual REGION proxies explicitly retain.5 preset.
 distance_scale=.5 if p['source_producers']==['REGION'] else 1.0;assert len(p['source_producers'])==1
 original=p['source_records'][0];radius=original['sphere'][3];rawflags=next(r['raw_flags'] for r in p['source_records'] if r['raw_flags']==8)
 cell['ranges'].append(struct.pack('<4I6fIf',300,cell['ni'],42,rawflags,*t,radius,*lohi[0],source_id,distance_scale));cell['vertices'].append(data.tobytes());cell['indices'].append((ix+cell['nv']).astype('<u4').tobytes());cell['nv']+=nv;cell['ni']+=42;cell['proxy_sources'].append(p['source_index'])
 proxy_proof.append(dict(source_index=p['source_index'],wire_source_index=source_id,producer=p['source_producers'],anchor_cell=list(anchor),full_source_pose=p,vertices=28,triangles=14,distance_scale=distance_scale,vertex_sha256=sha(data.tobytes()),wind_direction_full_float=True,phase_values=sorted(set(phase.astype(int).tolist()))))
assert sum(len(c['proxy_sources']) for c in cells.values())==34
# Source-owned REGION visibleleaf replacement IDs. Exactfullpose or uniqueanchor
# partrotation join is permitted only with explicit visible/shadow group evidence.
regprov=json.loads((A/'instance-audit/tree-gap-producer/region-aux-full-source-provenance.json').read_text());region_matches={};ambiguities=[]
for r in regprov:
 if r['fab']!=343974 or r['family']!=6 or r['assembly'] not in scene_asms:continue
 anchor=anchorkey(r);proxy=unitanchor.get(anchor)
 if proxy is None or proxy['source_producers']!=['REGION']:continue
 competing={fullkey(p) for p in anchor_candidates[anchor]}
 if len(competing)!=1:ambiguities.append(dict(source_index=r['source_index'],reason='competingproxyrotations',count=len(competing)));continue
 assert all(r['assembly'] not in g['element_indices'] for g in fabmetadata['groups'] if 5<=g['group']<=8)
 cell=tuple(int(x) for x in np.floor(np.array(proxy['translation'][:2])/6400));region_matches[r['source_index']]=dict(region_source_index=r['source_index'],proxy_source_index=proxy['source_index'],proxy_anchor_cell=list(cell),join='exactFullPose' if fullkey(r)==fullkey(proxy) else 'sameFAB/rawT/scale; visiblegroup1..4; exactlyoneproxyFullTQS acrossallsource',assembly=r['assembly'],original_flags=r['raw_flags'],source=r)
assert len(region_matches)==26 and sum(x['join']!='exactFullPose' for x in region_matches.values())==6 and not ambiguities
region_index=(W/'region-index.bin').read_bytes();assert region_index[:8]==b'OARGIDX1' and struct.unpack_from('<I',region_index,12)[0]==300
rpatches=[];marked=collections.Counter();missing_unrelated_region_cells=[];metadata_only_region_cells=[]
required_region_cells={tuple(output['cell']) for match in region_matches.values() for output in match['source']['outputs']}
for i in range(struct.unpack_from('<I',region_index,8)[0]):
 cx,cy,registered_triangles=struct.unpack_from('<2iI',region_index,24+40*i);fn=f'r{cx}_{cy}.bin'
 if registered_triangles==0:
  metadata_only_region_cells.append([cx,cy]);continue
 if (cx,cy) not in required_region_cells:
  if not (W/fn).exists():missing_unrelated_region_cells.append(fn)
  continue
 b=(W/fn).read_bytes();magic,nv2,ni2,nd2,vs,rs=struct.unpack_from('<8s5I',b);assert magic==b'OARGEO1\0' and vs==76 and rs==48;patch=bytearray(b);changed=[]
 for j in range(nd2):
  mat,first,count,flags,*rest=struct.unpack_from('<4I6fIf',b,28+48*j);sid=struct.unpack_from('<I',b,28+48*j+40)[0]
  if sid not in region_matches:continue
  assert mat==293 and count%3==0;struct.pack_into('<I',patch,28+48*j+12,flags|0x80000000);marked[sid]+=1;changed.append(dict(draw=j,source_index=sid,triangles=count//3,old_flags=flags,new_flags=flags|0x80000000))
 if changed:
  allowed={28+48*x['draw']+k for x in changed for k in range(12,16)};assert all(a==z or j in allowed for j,(a,z) in enumerate(zip(b,patch)));assert b[28+48*nd2:]==patch[28+48*nd2:];(O/fn).write_bytes(patch);rpatches.append(dict(file=fn,input_sha256=sha(b),output_sha256=sha(patch),geometry_header_and_other_range_bytes_exact=True,changes=changed))
assert set(marked)==set(region_matches)
replacement=struct.pack('<8sI',b'OASHR01\0',len(region_matches))+b''.join(struct.pack('<Iii',sid,*region_matches[sid]['proxy_anchor_cell']) for sid in sorted(region_matches));assert len(replacement)==12+12*len(region_matches);(O/'shadow-replacements.bin').write_bytes(replacement)
dep_rows=sorted({(*cell,*anchor) for cell,anchors in dependencies.items() for anchor in anchors});dep_blob=struct.pack('<8sI',b'OASHD01\0',len(dep_rows))+b''.join(struct.pack('<4i',*row) for row in dep_rows);assert len(dep_blob)==12+16*len(dep_rows);(O/'shadow-cell-deps.bin').write_bytes(dep_blob)
files=[];registry=[]
for (cx,cy),c in sorted(cells.items()):
 vd=b''.join(c['vertices']);ind=b''.join(c['indices']);ranges=b''.join(c['ranges']);nv3,ni3,nd3=c['nv'],c['ni'],len(c['ranges']);assert len(vd)==76*nv3 and len(ind)==ni3*4 and len(ranges)==nd3*48
 verts=np.frombuffer(vd,DT);lo=verts['v'][:,:3].min(0);hi=verts['v'][:,:3].max(0);blob=struct.pack('<8s5I',b'OARGEO1\0',nv3,ni3,nd3,76,48)+ranges+vd+ind
 parsed_ix=np.frombuffer(blob,'<u4',ni3,28+48*nd3+76*nv3);assert parsed_ix.max(initial=0)<nv3
 cursor=0
 for j in range(nd3):
  run=struct.unpack_from('<4I6fIf',blob,28+48*j);assert run[1]==cursor and run[0]<301 and run[2]%3==0;cursor+=run[2]
 assert cursor==ni3
 fn=f's{cx}_{cy}.bin';(O/fn).write_bytes(blob);registry.append(struct.pack('<iiII6f',cx,cy,ni3//3,nd3,*lo,*hi));files.append(dict(file=fn,cell=[cx,cy],bytes=len(blob),sha256=sha(blob),vertices=nv3,triangles=ni3//3,ranges=nd3,fallback_triangles=c['fallback_triangles'],proxy_sources=c['proxy_sources'],bounds=[lo.tolist(),hi.tolist()]))
shadow_index=struct.pack('<8sIIfI',b'OARGIDX1',len(files),301,1.0,0)+b''.join(registry);(O/'shadow-index.bin').write_bytes(shadow_index)
leafpatch=bytearray(li);struct.pack_into('<I',leafpatch,16,301);assert leafpatch[:16]==li[:16] and leafpatch[20:]==li[20:];(O/'leaf-index.bin').write_bytes(leafpatch)
regionpatch=bytearray(region_index);struct.pack_into('<I',regionpatch,12,301);assert regionpatch[:12]==region_index[:12] and regionpatch[16:]==region_index[16:];(O/'region-index.bin').write_bytes(regionpatch)
report=dict(status='Stagingonly, UNIT34sourceproxies; no live writes',material_row=300,material_count=301,family=10,proxy_alpha_texture=703,unit_proxy_poses=34,withheld_nonunit_proxy_poses=22,cells=len(files),fallback_source_cells=175,fallback_original_triangles=51831,fallback_retained_triangles=50506,fallback_removed_triangles=1325,proxy_triangles=476,total_shadow_triangles=sum(f['triangles'] for f in files),vertices=sum(f['vertices'] for f in files),max_ranges=max(f['ranges'] for f in files),bytes=sum(f['bytes'] for f in files)+len(shadow_index)+len(replacement)+len(dep_blob),source_leaf_ownership_one_to_one=True,source_inputs=inputs,space_proxy_matches=space_matches,fallback_proof=fallback_proof,proxy_provenance=proxy_proof,region_replacement_sources=list(region_matches.values()),region_rotation_variant_joins=sum(r['join']!='exactFullPose' for r in region_matches.values()),region_flag_patches=rpatches,region_replacement_count=len(region_matches),region_replacements_sha256=sha(replacement),shadow_index_sha256=sha(shadow_index),shadow_cell_dependency_count=len(dep_rows),shadow_cell_dependencies_sha256=sha(dep_blob),header_patches=[dict(file='leaf-index.bin',input_sha256=sha(li),output_sha256=sha(leafpatch),only_changed_u32_offset=16,old_count=300,new_count=301),dict(file='region-index.bin',input_sha256=sha(region_index),output_sha256=sha(regionpatch),only_changed_u32_offset=12,old_count=300,new_count=301)],space_fallback_proxy_readiness_dependencies=[dict(cell=list(cell),required_proxy_anchor_cells=[list(a) for a in sorted(anchors)]) for cell,anchors in sorted(dependencies.items())],files=files,limits=['Casteronlystream; MAINdepthprepass/visibleleafgeometry unchanged.','22nonunitfullsourceproxyposes withheld; fullinventory retained,no generalization from2nativeunitanchors.','SPACEfallbackranges intentionallyunbounded,explicitdistanceScale1; preservesallnativeleafpositivegeometry.','Proxyranges useauthoredadjacentbandunion0..30000;SPACE1,REGION.5explicitprovisionalpreset.','REGIONflag0x80000000onlyhonoredwhenmappedproxyanchorGPU+texturesready; preserveallother31flagbits.','SPACEcasterfallback usableonlywhenownGPUandALLshadow-cell-deps anchorGPU/texture states ready; preserveoldTREE_LEAFfallbackuntilthen.','Globalindextexturecount704patch ownedbyparent; neverwritebaseindex/rockmetadata here.','FullfloatworldwindN; nohalfquantization;sourceUV0/RGBA byteexact,sourceT/Bunusedzero.'])
assert report['total_shadow_triangles']==50982
report['missing_unrelated_live_region_cells']=missing_unrelated_region_cells
report['intentional_metadata_only_region_cells']=metadata_only_region_cells
(Q/'manifest.json').write_text(json.dumps(report,indent=2,default=lambda x:x.item()));print(json.dumps({k:v for k,v in report.items() if k not in ['source_inputs','space_proxy_matches','fallback_proof','proxy_provenance','region_replacement_sources','region_flag_patches','header_patches','files','space_fallback_proxy_readiness_dependencies']},indent=2,default=lambda x:x.item()))
