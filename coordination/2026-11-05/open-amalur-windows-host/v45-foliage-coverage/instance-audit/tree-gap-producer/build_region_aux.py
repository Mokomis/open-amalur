"""Source-backed indexed regional geometry candidate; never writes live assets.

OARGEO1 uses complete native source records with authored squared-distance
ranges. The registry's0.5 quality scale is a capture-fit inference, not a
recovered universal engine default. Different ranges/assemblies are retained.
"""
from pathlib import Path
import collections,hashlib,json,struct,sys
import numpy as np

sys.dont_write_bytecode = True
P = Path.home()/'Documents/Opem Amalur'
Q = Path(__file__).resolve().parent
W = P/'work/v40-windows-host/assets/world'
FULL = '--full' in sys.argv
O = Q/('candidate-world-full' if FULL else 'candidate-world')
O.mkdir(exist_ok=True)
S = json.loads((P/'work/v20-inputs/symbols.json').read_text())
rows = json.loads((Q/'region-collection-records.json').read_text())
inventory = json.loads((Q/'region-visible-source-inventory.json').read_text())
selected = {r['source_index'] for r in inventory['records']}
visible = {tuple(c) for c in json.loads((P/'work/v45-foliage-coverage/visible-cells.json').read_text())}
ib = (W/'index.bin').read_bytes()
base_count = struct.unpack_from('<I',ib,8)[0]
base_cells = {struct.unpack_from('<2i',ib,20+i*48) for i in range(base_count)}
state = json.loads((P/'work/v44-native-fidelity/foliage-research/material-state-audit/native-material-state-audit.json').read_text())['rows']
profiles = {x['native_material']:x for x in state}
profiles[343630] = dict(material=296,family=1)
profiles[1611839] = dict(material=297,family=1)
leaf_profiles = {r['native_material']:r for r in json.loads((P/'work/v44-native-fidelity/foliage-research/native-leaf-material-profiles.json').read_text())['rows']}
DT = np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')])
assert DT.itemsize == 76

def sha(b):
    return hashlib.sha256(b).hexdigest()

def find(name):
    return next((P/'work/v20-inputs'/a/name for a in ['patch_0.pak','initial_0.pak','DATA_0.pak'] if (P/'work/v20-inputs'/a/name).exists()),None)

def qr(q,v):
    u = np.array(q[:3])
    t = 2*np.cross(u,v)
    return v+q[3]*t+np.cross(u,t)

def mesh(path):
    b = path.read_bytes()
    na,nv,ni = struct.unpack_from('<3I',b)
    at,vertices,indices = 12,[],[]
    for _ in range(nv):
        _,stride,count = struct.unpack_from('<3I',b,at)
        at += 12
        vertices.append((at,stride,count))
        at += stride*count
    for _ in range(ni):
        count = struct.unpack_from('<I',b,at)[0]
        at += 4
        indices.append((at,count))
        at += 2*count
    assemblies = [struct.unpack_from('<HHI',b,at+i*52) for i in range(na)]
    assert at+52*na == len(b)
    return b,vertices,indices,assemblies

def identity(fab,rr,ph):
    material,assembly = struct.unpack_from('<2I',rr,64)
    # Derived bounds and collection-local record ordinals are not identity.
    # Native material, assembly, exact T/Q/S, range and flags ARE identity.
    return struct.pack('<3I',fab,material,assembly)+rr[16:28]+rr[32:60]+ph[64:76]

space_keys = {}
space_sources = []
for sid,name in S['simspace'].items():
    if not name.startswith('out_dal_'):
        continue
    path = find(sid+'.space_bxml')
    if path is None:
        continue
    raw = path.read_bytes()
    b = raw[8:8+struct.unpack_from('<I',raw)[0]]
    def array(slot,stride):
        ptr,n = struct.unpack_from('<2I',b,slot)
        assert ptr >= 8 and ptr-8+n*stride <= len(b)
        return [b[ptr-8+i*stride:ptr-8+(i+1)*stride] for i in range(n)]
    for group,(refslot,physslot,renderslot) in enumerate([(0x128,0x148,0x150),(0x130,0x158,0x160),(0x138,0x168,0x170),(0x140,0x178,0x180)]):
        refs,phys,renders = array(refslot,16),array(physslot,80),array(renderslot,84)
        assert len(refs) == len(phys) == len(renders)
        for i,(ref,ph,rr) in enumerate(zip(refs,phys,renders)):
            fab = struct.unpack_from('<I',ref,8)[0]
            key = identity(fab,rr,ph)
            space_keys.setdefault(key,[]).append(dict(space=int(sid),group=group,record=i))
    space_sources.append(dict(source=str(path.relative_to(P)),sha256=sha(raw)))

cache,cells,provenance = {},{},[]
seen,duplicates,space_duplicates = {},[],[]
stats = collections.Counter()
mat_tri = collections.Counter()
dropped_cells = collections.Counter()
for source_index,s in enumerate(rows):
    if source_index not in selected:
        continue
    rr = bytes.fromhex(s['render_record_hex'])
    ph = bytes.fromhex(s['physics_record_hex'])
    key = identity(s['fab'],rr,ph)
    if key in space_keys:
        space_duplicates.append(dict(source_index=source_index,space_witnesses=space_keys[key]))
        stats['exact_space_record_duplicates_skipped'] += 1
        continue
    if key in seen:
        duplicates.append(dict(source_index=source_index,canonical_source_index=seen[key]))
        stats['exact_regional_record_duplicates_skipped'] += 1
        continue
    seen[key] = source_index
    fid,mid,ai = s['fab'],s['material'],s['assembly']
    assert mid in profiles,mid
    profile = profiles[mid]
    if fid not in cache:
        path = find(str(fid)+'.fab_visual_data_streamable_bin')
        assert path is not None,fid
        cache[fid] = (*mesh(path),path)
    raw,vbs,ibs,assemblies,path = cache[fid]
    vi,_,ii = assemblies[ai]
    at,stride,nv = vbs[vi]
    assert stride in [48,56],(fid,ai,stride)
    ia,nindex = ibs[ii]
    ix = np.frombuffer(raw,'<u2',nindex,ia).astype('<u4').reshape(-1,3)
    local = np.ndarray((nv,3),'<f4',raw,at,(stride,4)).astype(float)
    B,t = np.array(s['basis']),np.array(s['translation'])
    q = s['quaternion']
    cq = (-q[0],-q[1],-q[2],q[3])
    scale = np.array(s['scale'])
    world = local@B+t
    uv = np.ndarray((nv,2),'<f4',raw,at+12,(stride,4))
    uv2 = np.ndarray((nv,2),'<f4',raw,at+20,(stride,4)) if stride == 56 else uv
    no = 20 if stride == 48 else 28
    safe = np.where(abs(scale)>1e-4,scale,1)
    frames = []
    for off in [no,no+8,no+16]:
        vec = np.ndarray((nv,3),'<i2',raw,at+off,(stride,2)).astype(float)/safe
        vec /= np.maximum(np.linalg.norm(vec,axis=1,keepdims=True),1e-9)
        frames.append(qr(cq,vec))
    flags = np.full(nv,3,'<u4')
    if profile['family'] == 6:
        params = leaf_profiles[mid]['parameters']
        radial = world-t
        radial[:,2] -= params['CenterZOffset']
        if params['UseSphericalNormals'] < .5:
            radial[:,2] = 0
        radius = np.linalg.norm(radial,axis=1).astype('<f4')
        frames[0] = radial/np.maximum(radius[:,None],1e-9)
        for k,off in [(1,no+8),(2,no+16)]:
            frames[k] = np.maximum(np.ndarray((nv,3),'<i2',raw,at+off,(stride,2)).astype(float)/32767,-1)
        normal = np.ndarray((nv,3),'<i2',raw,at+no,(stride,2)).astype(float)
        normal /= np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-9)
        wind_dir = qr(cq,normal*scale)
        ab = np.abs(local.astype('<f4'))
        phase = np.float32(np.float32(ab[:,0]+ab[:,1])+ab[:,2])*np.float32(.1)
        phase = np.float32(phase-np.floor(phase))
        phase = np.uint32(np.float32(phase*np.float32(10)))
        packed = np.c_[wind_dir,phase.astype('<f4')].astype('<f2').copy().view('<u4').reshape(nv,2)
        assert np.array_equal(packed.copy().view('<f2').reshape(nv,4)[:,3].astype('<u4'),phase)
        uv2 = packed.copy().view('<f4')
        flags = radius.copy().view('<u4')
    data = np.empty(nv,DT)
    data['v'] = np.concatenate([world,*frames,uv,uv2],axis=1).astype('<f4')
    data['rgba'] = np.ndarray((nv,4),'u1',raw,at+stride-4,(stride,1))
    data['material'] = mid
    data['flags'] = flags
    assert np.array_equal(data['v'][:,12:14].view('<u4'),uv.copy().view('<u4'))
    assert np.array_equal(data['rgba'],np.ndarray((nv,4),'u1',raw,at+stride-4,(stride,1)))
    cc = np.floor(world[ix].mean(1)[:,:2]/6400).astype(int)
    outputs = []
    count_kept = 0
    for cell in sorted({tuple(c) for c in cc}):
        mask = np.all(cc==cell,axis=1)
        tris = ix[mask]
        if cell not in base_cells and not FULL:
            dropped_cells[cell] += len(tris)
            stats['triangles_outside_base1271_skipped'] += len(tris)
            continue
        used,inv = np.unique(tris.ravel(),return_inverse=True)
        verts = data[used].copy()
        dest = cells.setdefault(cell,dict(vertices=[],indices=[],ranges=[],vertex_count=0,index_count=0))
        indices = inv.astype('<u4')+dest['vertex_count']
        assert np.array_equal(verts['v'][inv,:3],data['v'][tris.ravel(),:3])
        assert np.array_equal(verts['v'][inv,12:14],data['v'][tris.ravel(),12:14])
        sphere = struct.unpack_from('<4f',rr)
        anchor = [*s['translation'],sphere[3]]
        lo,hi = s['distance_squared_fields']
        run = struct.pack('<4I6fIf',profile['material'],dest['index_count'],len(indices),s['physics_flags'],*anchor,lo,hi,source_index,0.0)
        assert len(run) == 48
        dest['ranges'].append(run)
        dest['vertices'].append(verts.tobytes())
        dest['indices'].append(indices.tobytes())
        dest['vertex_count'] += len(verts)
        dest['index_count'] += len(indices)
        count_kept += len(tris)
        outputs.append(dict(cell=list(map(int,cell)),triangles=len(tris),vertices=len(verts)))
    if outputs:
        stats['records_emitted'] += 1
        stats['triangles_emitted'] += count_kept
        mat_tri[mid] += count_kept
        provenance.append(dict(source_index=source_index,rank=s['group'],source_identity_sha256=sha(key),region=431608,group=s['group'],record=s['record'],fab=fid,fab_name=s['name'],native_material=mid,material_row=profile['material'],family=profile['family'],assembly=ai,translation=s['translation'],quaternion=s['quaternion'],scale=s['scale'],raw_flags=s['physics_flags'],distance_squared=s['distance_squared_fields'],per_range_distance_scale=0.0,actual_source_sphere=list(sphere),lod_anchor=anchor,reference_record_hex=s['reference_record_hex'],physics_record_hex=s['physics_record_hex'],render_record_hex=s['render_record_hex'],mesh_source=str(path.relative_to(P)),mesh_sha256=sha(raw),source_vertex_sha256=sha(raw[at:at+nv*stride]),source_index_sha256=sha(raw[ia:ia+2*nindex]),source_index_count=nindex,outputs=outputs))

files,registry = [],[]
for (cx,cy),cell in sorted(cells.items()):
    vd = b''.join(cell['vertices'])
    ind = b''.join(cell['indices'])
    ranges = b''.join(cell['ranges'])
    nv,ni,nd = cell['vertex_count'],cell['index_count'],len(cell['ranges'])
    assert len(vd) == nv*76 and len(ind) == ni*4 and len(ranges) == nd*48
    assert nd <= 4096
    verts = np.frombuffer(vd,DT)
    lo,hi = verts['v'][:,:3].min(0),verts['v'][:,:3].max(0)
    blob = struct.pack('<8s5I',b'OARGEO1\0',nv,ni,nd,76,48)+ranges+vd+ind
    # Reparse run offsets and index bounds independently of the serializer.
    parsed = struct.unpack_from('<8s5I',blob)
    assert parsed == (b'OARGEO1\0',nv,ni,nd,76,48)
    indices = np.frombuffer(blob,'<u4',ni,28+48*nd+76*nv)
    assert indices.max(initial=0) < nv
    at = 0
    for i in range(nd):
        run = struct.unpack_from('<4I6fIf',blob,28+48*i)
        assert run[1] == at and run[2]%3 == 0 and run[0] < 299 and run[-1] == 0
        at += run[2]
    assert at == ni
    file = f'r{cx}_{cy}.bin'
    (O/file).write_bytes(blob)
    registry.append(struct.pack('<iiII6f',cx,cy,ni//3,nd,*lo,*hi))
    files.append(dict(file=file,cell=[cx,cy],triangles=ni//3,vertices=nv,draws=nd,bytes=len(blob),sha256=sha(blob),bounds=[lo.tolist(),hi.tolist()],in_original_visible203=(cx,cy) in visible))
index = struct.pack('<8sIIfI',b'OARGIDX1',len(files),299,.5,0)+b''.join(registry)
assert len(index) == 24+40*len(files)
(O/'region-index.bin').write_bytes(index)
stats['vertices_emitted'] = sum(x['vertices'] for x in files)
stats['draw_ranges_emitted'] = sum(x['draws'] for x in files)
stats['bytes_emitted'] = sum(x['bytes'] for x in files)+len(index)
provenance_file = 'region-aux-full-source-provenance.json' if FULL else 'region-aux-source-provenance.json'
manifest_file = 'region-aux-stage-full-manifest.json' if FULL else 'region-aux-stage-manifest.json'
manifest = dict(status='isolated candidate; no basecell/livepack edits',format='OARGEO1 indexed76Bvertices/48Branges; OARGIDX1 registry24B+40Bcells',source_region='work/v20-inputs/patch_0.pak/431608.region_bxml',source_region_sha256=sha((P/'work/v20-inputs/patch_0.pak/431608.region_bxml').read_bytes()),material_count=299,registry_distance_scale=.5,distance_scale_evidence='Explicitprovisionaloriginalqualitypreset:0.5*originDistance fits97/97 originalcapturedregionaltree drawgeometrycandidate sets;nativeconsumerfactorunrecovered. Per-range0inheritsregistry. Actorpacksuse1orper-range1.',counts=dict(stats),files=files,index_sha256=sha(index),material_triangles=[dict(native_material=m,material_row=profiles[m]['material'],family=profiles[m]['family'],triangles=n) for m,n in mat_tri.most_common()],exact_region_duplicates=duplicates,exact_space_duplicates=space_duplicates,space_source_files=space_sources,source_provenance=provenance_file,dropped_outside_base_cells=[dict(cell=list(map(int,c)),triangles=n) for c,n in sorted(dropped_cells.items())],includes_region_only_cells=FULL,new_cells_outside_base1271=[f['cell'] for f in files if tuple(f['cell']) not in base_cells],selection='Allauthorednonshadow/nonwaterregionalrecordswith≥1trianglecentroidin203visiblecells;whole selectedrecords includingnewauxcells.' if FULL else 'Allauthorednonshadow/nonwaterregionalrecordswith≥1trianglecentroidin203visiblecells;entireselectedrecord retainedexceptcentroidcellsabsentfrom1271baseindex.',dedup='ExactnativeFab+MID+assembly+bitwiseRAW T/Q/S+minSq/maxSq+rawflags only. Differentassemblies/materials/ranges neverdeduped. Compareall4authoredSPACEcollectionsagainstregionrecords.',vertex_contract='BodyN/T/B inverse-transpose normalizedlikeestablishedstaticproducer. Leafnative radialN,pivotRAW T,CenterZOffset,T/BsourceSNORMunchanged,RGBAbyteexact,UV0bitexact,UV1halfpackedwinddirection/phase,flagsfloatradialLength. WorldPdirectnativeTRS, no spherepivotre-scaling.',validation='Per-recordUV/RGBAexact; indexedremapP/UVexact; completeeveryfileheader/range/indexreparse; originalsourceVB/IB/fullrawrecords+SHA retained.',limits=['Rootreviewsandmergesmaterialrows296/297andtextures685..691;4002normalreusesbitexact668.','Rootmergecannotoverwritec*.bin,mossfixoroldl*.bin.','Rootoptionalregistryloader mustsupportregion-onlycells.' if FULL else 'Onlybase1271centroidcellssupported; omittedout-of-base trianglesreported.','Authoreddistancebandsretained,notallLODssimultaneous.','Shadow/watermaterialsintentionallyexcluded; existingwaterfallsuntouched.'])
(Q/provenance_file).write_text(json.dumps(provenance,indent=2))
(Q/manifest_file).write_text(json.dumps(manifest,indent=2,default=lambda value:value.item()))
print(json.dumps(dict(counts=dict(stats),cells=len(files),max_draws=max(x['draws'] for x in files),materials=manifest['material_triangles'],duplicates=[len(duplicates),len(space_duplicates)],registry_sha256=sha(index)),indent=2))
