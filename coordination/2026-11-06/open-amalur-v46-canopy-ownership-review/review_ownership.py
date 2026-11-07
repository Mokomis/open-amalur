from pathlib import Path
import json,struct,hashlib,collections,sys
import numpy as np
R=Path(r'C:\Users\rwill\Documents\Opem Amalur');A=R/'work/v45-foliage-coverage';Q=R/'work/v46-canopy';W=R/'work/v40-windows-host/assets/world';D=Q/'candidate-world';O=Q/'ownership-review';O.mkdir(exist_ok=True)
prov=json.loads((A/'expanded-leaf-attributes/source-provenance.json').read_text());direct=json.loads((A/'native-leaf-direct-trs/manifest.json').read_text());lookup={x['file']:x for x in direct['files']};offset=json.loads((A/'native-leaf-direct-trs/source-instance-offsets.json').read_text());selected=set(json.loads((A/'native-leaf-direct-trs/proven-only-manifest.json').read_text())['selected_source_indices'])
DT=np.dtype([('v','<f4',(16,)),('c','u1',(4,)),('mid','<u4'),('flags','<u4')]);soup=(A/'expanded-leaf-attributes/leaf-source-attributes.oawt').read_bytes();snv=struct.unpack_from('<I',soup,12)[0];SV=np.frombuffer(soup,DT,snv,20).reshape(-1,3)
cumulative=np.cumsum([x['triangles'] for x in prov]);owner=np.searchsorted(cumulative,np.arange(len(SV)),side='right');assert len(prov)==590 and len(SV)==51831
sourcefilecache={};source_records_verified=0
for p in prov:
 sid=p['space']
 if sid not in sourcefilecache:
  f=next(R/'work/v20-inputs'/a/(str(sid)+'.space_bxml') for a in ['patch_0.pak','initial_0.pak','DATA_0.pak'] if (R/'work/v20-inputs'/a/(str(sid)+'.space_bxml')).exists());sourcefilecache[sid]=f.read_bytes()
 assert sourcefilecache[sid].find(bytes.fromhex(p['render_record_hex']))>=0;source_records_verified+=1
li=(W/'leaf-index.bin').read_bytes();nc,nm,mc=struct.unpack_from('<III',li,8);assert nc==175 and mc==301
seen=np.zeros(len(SV),np.int32);stats=collections.Counter();files=[];spacecounts=collections.Counter();maxposerr=0
for k in range(nc):
 cx,cy,nt=struct.unpack_from('<iiI',li,20+8*nm+12*k);fn=f'l{cx}_{cy}.bin';b=(W/fn).read_bytes();n=(D/fn).read_bytes();magic,nv,ni,nd=struct.unpack_from('<4sIII',b);assert magic==b'OAWE';omagic,nnv,nni,nnr,stride,rs=struct.unpack_from('<8s5I',n);assert(omagic,nnv,nni,stride,rs)==(b'OARGEO1\0',nv,ni,76,48);assert nnr<=4096 and len(n)==28+48*nnr+nv*76+ni*4;assert n[28+48*nnr:]==b[16+12*nd:];assert nt==ni//3
 V=np.frombuffer(b,DT,nv,16+12*nd);I=np.frombuffer(b,'<u4',ni,16+12*nd+nv*76);assert np.all(I<nv);tm=np.full(nt,0xffffffff,'<u4');coverage=np.zeros(nt,np.uint8)
 for j in range(nd):
  mat,first,count=struct.unpack_from('<III',b,16+j*12);assert mat<mc and first%3==count%3==0 and first+count<=ni;tm[first//3:(first+count)//3]=mat;coverage[first//3:(first+count)//3]+=1
 assert np.all(coverage==1)
 original=np.array(lookup[fn]['source_triangles']);assert len(original)==nt and original.min()>=0 and original.max()<len(SV);seen[original]+=1
 own=owner[original];expected_spaces=np.array([prov[x]['space'] for x in own]);tri=V[I.reshape(-1,3)];source=SV[original]
 # Independently prove source triangle correspondence by UV+color+MID and position.
 assert np.array_equal(tri['v'][:,:,12:14],source['v'][:,:,12:14]);assert np.array_equal(tri['c'],source['c']);assert np.array_equal(tri['mid'],source['mid'])
 target=source['v'][:,:,:3].astype(float).copy()
 for sid in np.unique(own):
  if sid in selected:target[own==sid]+=np.array(offset[sid]['correction_cm'])
 err=float(np.max(abs(tri['v'][:,:,:3]-target)));assert err<.05,(fn,err);maxposerr=max(maxposerr,err)
 cursor=0;newcover=np.zeros(nt,np.uint8)
 for j in range(nnr):
  mat,first,count,flags,*z=struct.unpack_from('<4I6fIf',n,28+j*48);sphere=z[:4];lo,hi=z[4:6];space=int(z[6]);scale=z[7]
  assert first==cursor and count>0 and count%3==first%3==0 and first+count<=ni;assert mat<mc and flags==0x40000000;assert sphere==[0,0,0,0] and lo==0 and hi==float(np.finfo(np.float32).max) and scale==1
  a,bb=first//3,(first+count)//3;assert np.all(tm[a:bb]==mat) and np.all(expected_spaces[a:bb]==space);assert space in sourcefilecache and space!=0;newcover[a:bb]+=1;spacecounts[space]+=count//3;cursor+=count
 assert cursor==ni and np.all(newcover==1)
 stats.update(files=1,triangles=nt,ranges=nnr,vertices=nv);stats['max_ranges']=max(stats['max_ranges'],nnr);files.append({'file':fn,'old_sha256':hashlib.sha256(b).hexdigest(),'candidate_sha256':hashlib.sha256(n).hexdigest(),'triangles':nt,'ranges':nnr,'source_position_max_error_cm':err})
assert np.all(seen==1);assert sum(spacecounts.values())==51831
# Native33 positive source-Space crosscheck, independent of candidate range construction.
native=json.loads((A/'instance-audit/native-tree-source-correspondence.json').read_text());raw=json.loads((A/'instance-audit/raw-render-translation-vs-native-audit.json').read_text());raw={x['draw']:x for x in raw['rows']};positives=[]
for d in native:
 if d['vs']!=877:continue
 if not raw[d['draw']]['same_fab_basis_raw_translation_matched']:continue
 T=np.array(d['native_world_matrix'][12:15]);fabs={x['fab'] for x in d['source_assembly_candidates']};matches=[]
 for j,p in enumerate(prov):
  if p['fab'] not in fabs:continue
  t=np.array(struct.unpack_from('<3f',bytes.fromhex(p['render_record_hex']),16))
  if np.max(abs(t-T))<.02:matches.append({'source_instance':j,'space':p['space'],'fab':p['fab'],'assembly':p['assembly']})
 assert matches,d['draw'];spaces=sorted({m['space'] for m in matches});r=raw[d['draw']]['best_same_fab_raw_translation'];assert raw[d['draw']]['same_fab_basis_raw_translation_matched'];assert r['space'] in spaces;assert all(s in spacecounts for s in spaces)
 positives.append({'draw':d['draw'],'native_fabs':sorted(fabs),'native_T':T.tolist(),'expanded_source_spaces':spaces,'independent_raw_source_space':r['space'],'matches':matches})
assert len(positives)==33
summary={'status':'Independent ownership candidate checks pass; no livepromotion','counts':dict(stats),'material_count':mc,'all_old_76B_vertices_and_u32indices_byteexact_ordered':True,'draw_coverage_no_gaps_overlaps_or_zero_runs':True,'all_51831_source_triangles_seen_exactly_once':True,'all_590_source_parts_cover_exact_original_triangle_counts':True,'all_590_source_record_hex_found_in_owning_original_SPACEfile':True,'independent_source_UV_RGBA_nativeMID_exact':True,'source_position_max_error_cm':maxposerr,'position_scope':'Originalsource soup +only5previouslyprovedTRScorrections; serializedposition tolerances<.05cm. Candidatevsoldpayload isbyteexact.','range_contract':'flag0x40000000,source=nonzeroowningnativeSPACEassetID,sphere0,min0,maxFLT_MAX,distanceScale1; noLODguess','space_triangle_counts':dict(spacecounts),'native_leaf_positive_draws':len(positives),'native_positive_space_counts':dict(collections.Counter(x['independent_raw_source_space'] for x in positives)),'native_positive_source_spaces_all_present':True,'scope':'Ownership/geometry provenance only. Sourceportal traversal/selectedSpace set remains rootintegration proof, not established by metadata alone.','stage_script_sha256':hashlib.sha256((Q/'stage_canopy_ownership.py').read_bytes()).hexdigest(),'files':files,'native_positive_checks':positives}
(O/'independent-ownership-review.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps({k:v for k,v in summary.items() if k not in ['files','native_positive_checks']},indent=2))
