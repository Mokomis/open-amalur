from pathlib import Path
import collections, hashlib, json, struct
import numpy as np

P=Path(r'C:\Users\rwill\Documents\Opem Amalur')
R=P/'work/v44-native-fidelity'
G=R/'static-overlay'
A=R/'foliage-research/lod-attributes'
OUT=G/'generation4'
W=OUT/'world'
W.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
dt=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')])
old_dt=np.dtype([('p','<f4',(3,)),('n','<i2',(4,)),('uv','<f4',(2,))])
graw=(G/'manifest.json').read_bytes();g3=json.loads(graw);assert g3['generation']==3
araw=(A/'lod-attribute-manifest.json').read_bytes();am=json.loads(araw)
gby={c['file']:c for c in g3['cells']}
material_index={r['native_material']:r['index'] for r in g3['new_material_indices']}
assert len(material_index)==33 and set(material_index.values())==set(range(263,296))

def read_cell(b,expected_magic):
    magic,nv,ni,nd=struct.unpack_from('<4s3I',b);assert magic==expected_magic
    draws=[struct.unpack_from('<3I',b,16+i*12) for i in range(nd)]
    vo=16+nd*12;stride=28 if magic==b'OAWC' else 76
    assert len(b)==vo+nv*stride+ni*4
    v=np.frombuffer(b,old_dt if stride==28 else dt,nv,vo)
    ix=np.frombuffer(b,'<u4',ni,vo+nv*stride)
    # v43 native terrain draws intentionally share the old ground index range.
    assert all(c%3==0 and first%3==0 and first+c<=ni for _,first,c in draws)
    return nv,ni,nd,draws,v,ix

receipts=[];totals=collections.Counter();new_water=collections.Counter()
for lodrow in am['lods']:
    lod=lodrow['lod'];assert lod in (1,2)
    for cell in lodrow['cells']:
        name=cell['source_cell'];x,y=cell['cell'];assert name==f'c{x}_{y}_{lod}.bin'
        path=R/'before-world'/name
        if not path.exists():path=P/'work/v40-windows-host/assets/world'/name
        raw=path.read_bytes();previous=gby.get(name)
        original_expected=previous['input_sha256'] if previous else cell['source_cell_sha256']
        assert sha(raw)==original_expected,(name,'original source SHA mismatch')
        nv,ni,nd,draws,v,ix=read_cell(raw,b'OAWC')
        river_offsets=set();g3_hash=None;g3_to_original={}
        if previous:
            assert previous['input_sha256']==sha(raw) and previous['static_joined']==0
            b=(G/'world'/name).read_bytes();g3_hash=sha(b);assert g3_hash==previous['sha256']
            gn,gi,gd,gdraw,gv,gix=read_cell(b,b'OAWE');assert gn==nv
            assert np.array_equal(gv['v'][:,:3],v['p']) and np.array_equal(gv['v'][:,12:14],v['uv'])
            kept=collections.defaultdict(collections.deque)
            for mat,first,count in gdraw:
                for o in range(first,first+count,3):kept[(mat,tuple(map(int,gix[o:o+3])))].append(o)
            for mat,first,count in draws:
                for offset in range(first,first+count,3):
                    key=(mat,tuple(map(int,ix[offset:offset+3])))
                    if kept[key]:g3_to_original[kept[key].popleft()]=offset
                    else:
                        assert mat in (62,63,64,206),(name,'unexpected previous removal',mat)
                        river_offsets.add(offset)
            assert not any(kept.values())
            assert len(river_offsets)==sum(previous['water_removed'].values())
            assert sum(c for _,_,c in draws)-len(river_offsets)*3==gi
            for draw,count in previous['water_removed'].items():new_water[(int(draw),lod)]+=count
        op=A/'cell-overlays'/name.replace('.bin','.oawt')
        overlay=op.read_bytes();assert sha(overlay)==cell['output_sha256']
        assert struct.unpack_from('<4s4I',overlay)==(b'OAWT',1,76,cell['joined']*3,0)
        ov=np.frombuffer(overlay,dt,offset=20).reshape(-1,3)
        rp=op.with_suffix('.remove.u32');rb=rp.read_bytes();offsets=np.frombuffer(rb,'<u4')
        offset_basis=cell['source_magic']
        if offset_basis=='OAWE':
            assert previous and cell['source_cell_sha256']==g3_hash
            offsets=np.array([g3_to_original[int(o)] for o in offsets],dtype='<u4')
        else:
            assert offset_basis=='OAWC' and cell['source_cell_sha256']==sha(raw)
        assert len(offsets)==len(ov) and len(set(map(int,offsets)))==len(offsets)
        owned=set(map(int,offsets));assert not owned.intersection(river_offsets)
        assert all(sum(first<=offset<first+count for _,first,count in draws)==1 for offset in owned|river_offsets)
        native=collections.OrderedDict()
        for tri,offset in zip(ov,offsets):
            offset=int(offset);assert offset%3==0 and 0<=offset<ni
            ids=ix[offset:offset+3]
            assert np.array_equal(tri['v'][:,:3],v['p'][ids])
            assert np.array_equal(tri['v'][:,12:14],v['uv'][ids])
            mid=int(tri['material'][0]);assert np.all(tri['material']==mid)
            native.setdefault(material_index[mid],[]).append(tri.copy())
        remove=owned|river_offsets
        expanded=np.zeros(nv,dt);expanded['v'][:,:3]=v['p']
        expanded['v'][:,3:6]=v['n'][:,:3].astype(np.float32)/32767.*(v['n'][:,3:4].astype(np.float32)/32767.)
        expanded['v'][:,12:14]=v['uv'];expanded['v'][:,14:16]=v['uv'];expanded['rgba'][:]=255
        outdraw=[];outix=[];cursor=0;retained_offsets=[]
        for mat,first,count in draws:
            keep=[offset for offset in range(first,first+count,3) if offset not in remove]
            if keep:
                ids=np.concatenate([ix[o:o+3] for o in keep]).astype('<u4')
                outdraw.append((mat,cursor,len(ids)));outix.append(ids);cursor+=len(ids);retained_offsets.extend(keep)
        added=[];vn=nv;native_bytes={}
        for index,tris in native.items():
            corners=np.concatenate(tris);added.append(corners);native_bytes[index]=corners.tobytes()
            ids=np.arange(vn,vn+len(corners),dtype='<u4')
            outdraw.append((index,cursor,len(ids)));outix.append(ids);cursor+=len(ids);vn+=len(corners)
        vertices=np.concatenate([expanded]+added);indices=np.concatenate(outix)
        assert len(indices)==sum(c for _,_,c in draws)-len(river_offsets)*3
        assert len(outdraw)<=128 and int(indices.max())<len(vertices)
        assert np.array_equal(vertices['v'][:nv,:3],v['p']) and np.array_equal(vertices['v'][:nv,12:14],v['uv'])
        blob=b'OAWE'+struct.pack('<3I',len(vertices),len(indices),len(outdraw))+b''.join(struct.pack('<3I',*d) for d in outdraw)+vertices.tobytes()+indices.tobytes()
        # Independent serialized reread: all 76 native bytes, including float-bitcast wind/radius words.
        on,oi,od,odraw,ovtx,oix=read_cell(blob,b'OAWE')
        for index,first,count in odraw:
            if index>=263:assert ovtx[oix[first:first+count]].tobytes()==native_bytes[index]
        assert ovtx[:nv].tobytes()==expanded.tobytes()
        assert len(retained_offsets)+len(owned)+len(river_offsets)==sum(c for _,_,c in draws)//3
        (W/name).write_bytes(blob)
        counts=collections.Counter(int(mid) for mid in ov['material'][:,0])
        leaf=sum(c for mid,c in counts.items() if mid in (359202,419060,559590))
        totals.update(cells=1,source_triangles=ni//3,retained_baseline_triangles=len(retained_offsets),native_coarse_triangles=len(ov),leaf_coarse_triangles=leaf,water_removed_triangles=len(river_offsets),output_triangles=len(indices)//3)
        receipts.append(dict(file=name,cell=[x,y],lod=lod,original_path=str(path),original_sha256=sha(raw),generation3_sha256=g3_hash,overlay_sha256=sha(overlay),removals_sha256=sha(rb),sha256=sha(blob),bytes=len(blob),vertices=len(vertices),indices=len(indices),draws=len(outdraw),triangles=len(indices)//3,original_triangles=ni//3,native_coarse_triangles=len(ov),leaf_coarse_triangles=leaf,water_removed_triangles=len(river_offsets),water_removed=previous['water_removed'] if previous else {},retained_baseline_triangles=len(retained_offsets),positions_uv0_exact=True,native_full76bytes_exact=True,baseline_full76bytes_exact=True,native_material_triangles=dict(counts)))

        receipts[-1]['input_removal_offset_basis']=offset_basis
        receipts[-1]['resolved_original_removal_offsets_sha256']=sha(offsets.astype('<u4').tobytes())

assert totals['cells']==36 and totals['native_coarse_triangles']==33911
assert sum(c['native_coarse_triangles'] for c in receipts if c['lod']==1)==28450
assert sum(c['native_coarse_triangles'] for c in receipts if c['lod']==2)==5461
affected=set(c['file'] for c in receipts)
combined_water=collections.Counter(new_water)
for c in g3['cells']:
    if c['file'] not in affected:
        for draw,count in c['water_removed'].items():combined_water[(int(draw),c['lod'])]+=count
expected=collections.Counter({(r['draw'],r['lod']):r['count'] for r in g3['all_lod_water_expected']})
assert combined_water==expected and sum(combined_water.values())==6494
manifest=dict(generation=4,scope='36 LOD1/2 cell-only incremental overlay over generation3; no automatic promotion',generation3_manifest_sha256=sha(graw),lod_attribute_manifest_sha256=sha(araw),material_mapping=material_index,material_count=296,textures_unchanged=True,materials_unchanged=True,totals=dict(totals),cells=receipts,all_lod_water_exactly_preserved=True,all_lod_water_removals=[dict(draw=d,lod=l,count=n) for (d,l),n in sorted(combined_water.items())],untouched_generation3_cells=[c['file'] for c in g3['cells'] if c['file'] not in affected],native_vertex_full76byte_verification=True,retained_original_vertices_positions_uv_exact=True)
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
patch=dict(format='metadata only; patch triangle count of these cells/lods into current integrated index; preserve all other header/record/grass fields',generation=4,cells=[dict(cell=c['cell'],lod=c['lod'],file=c['file'],triangles=c['triangles'],indices=c['indices'],sha256=c['sha256']) for c in receipts])
(OUT/'index-triangle-counts.json').write_text(json.dumps(patch,indent=2))
(OUT/'REPORT.md').write_text('''# Generation4 coarse native attributes\n\nDeploy only the 36 `world/c*.bin` files and patch per-cell/LOD triangle counts using `index-triangle-counts.json`. Materials, texture resources, terrain profiles, grass files, index header and grass metadata must remain the current integrated versions. No index.bin is supplied.\n\nAll cells were rebuilt from SHA-verified original before-world backups where present, otherwise verified unchanged baseline cells. Generation3 exact water removal index subsets were retained. Frozen coarse source-owned overlays replace the corresponding disjoint original triangle indices; all native 76-byte records, including packed leaf wind and radial-length bits, are checked byte-for-byte after serialized reread. Original retained vertex positions/UV0 and baseline-expanded 76-byte records are unchanged.\n\nThe 36 cells carry 28,450 LOD1 plus 5,461 LOD2 native source-owned triangles. They retain original coarse positions and UV0; shader attributes are propagated from their exact original source ancestors. This is the port global-cluster geometry, not a claim to original-game authored LOD meshes.\n\nAll 6,494 native-water legacy triangle removals across every LOD remain exact when these 36 files are combined with untouched generation3 cells. Prior generation files, live assets, core sources and original inputs were not modified.\n''')
print(json.dumps(dict(totals=dict(totals),all_lod_water=sum(combined_water.values()),manifest_sha256=sha((OUT/'manifest.json').read_bytes()),output=str(OUT)),indent=2))
