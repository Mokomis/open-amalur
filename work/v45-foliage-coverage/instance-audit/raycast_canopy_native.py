"""Three offline reference rays against captured tree draw geometry and alpha."""
from pathlib import Path
import sys,json,struct,math,numpy as np
sys.dont_write_bytecode = True
P = Path.home()/'Documents/Opem Amalur'
Q = Path(__file__).resolve().parent
W = P/'work/v40-windows-host/assets/world'
sys.path.insert(0,str(P/'work/v07-mesh'))
import amalur_mesh
meta = json.loads((P/'work/v44-native-fidelity/bridge-native-final-r2.json').read_text())
vp = np.array(meta['mvp_column_major']).reshape(4,4,order='F')
ivp = np.linalg.inv(vp)
width,height = meta['width'],meta['height']
pixels = [(500,35),(800,150),(980,210)]
draws = json.loads((Q/'all-source-poses/native-tree-source-correspondence.json').read_text())
color = {d['draw']:d for d in json.loads((Q/'all-native-leaf-color-residency.json').read_text())}
states = {d['native_material']:d for d in json.loads((P/'work/v44-native-fidelity/foliage-research/material-state-audit/native-material-state-audit.json').read_text())['rows']}
auth = {d['fab']:d for d in json.loads((Q/'authored-fab-groups.json').read_text())}
palette = np.array([.7793933749198914,.08575710654258728,.9925394058227539,.5854730606079102,.7862923741340637,.9102197885513306,.9908282160758972,.5957845449447632,.07477909326553345,.7626959681510925,0,0])
texcache,meshes = {},{}

def ray(pixel):
    x,y = pixel
    ndc = [2*(x+.5)/width-1,1-2*(y+.5)/height]
    a = ivp@np.array([*ndc,-1,1])
    b = ivp@np.array([*ndc,1,1])
    a,b = a[:3]/a[3],b[:3]/b[3]
    d = b-a
    return a,d/np.linalg.norm(d)

def texture(tid):
    if tid not in texcache:
        b = (W/f't{tid}.bin').read_bytes()
        _,w,h,n = struct.unpack_from('<4I',b,4)
        at,levels = 20,[]
        for _ in range(n):
            size = struct.unpack_from('<I',b,at)[0]
            at += 4
            levels.append(np.frombuffer(b,'u1',size,at).reshape(h,w,4))
            at += size
            w,h = max(1,w//2),max(1,h//2)
        texcache[tid] = levels
    return texcache[tid]

def sample(tid,uv,grad):
    levels = texture(tid)
    h,w,_ = levels[0].shape
    g = np.array(grad)*[w,h]
    lod = max(0,min(len(levels)-1,math.log2(max(np.linalg.norm(g[0]),np.linalg.norm(g[1]),1e-20))))
    def bilinear(im):
        h,w,_ = im.shape
        x,y = np.array(uv)*[w,h]-.5
        ix,iy = math.floor(x),math.floor(y)
        a,b = x-ix,y-iy
        return ((im[iy%h,ix%w]*(1-a)+im[iy%h,(ix+1)%w]*a)*(1-b)+(im[(iy+1)%h,ix%w]*(1-a)+im[(iy+1)%h,(ix+1)%w]*a)*b)/255
    lo = int(lod)
    hi = min(lo+1,len(levels)-1)
    value = bilinear(levels[lo])*(1-(lod-lo))+bilinear(levels[hi])*(lod-lo)
    return dict(lod=lod,rgba=value.tolist())

rays = [ray(p) for p in pixels]
hits = [[] for p in pixels]
for d in draws:
    option = d['source_assembly_candidates'][0]
    fid,ai = option['fab'],option['assembly']
    if fid not in meshes:
        path = P/option['source']
        meshes[fid] = (amalur_mesh.parse_file(path),path.read_bytes())
    mesh,raw = meshes[fid]
    asm = mesh['assemblies'][ai]
    vb = mesh['vertex_buffers'][asm['vertex_buffer']]
    assert vb['data_sha256'] == option['vertex_sha256']
    index = np.array(mesh['index_buffers'][asm['index_buffer']]['indices'])
    index = index[d['native_first_index']:d['native_first_index']+d['native_index_count']]+d['native_base_vertex']
    ix = index.reshape(-1,3)
    local = np.array(vb['positions'])
    M = np.array(d['native_world_matrix']).reshape(4,4)
    world = local@M[:3,:3]+M[3,:3]
    uv = np.ndarray((len(local),2),'<f4',raw,vb['data_file_offset']+12,(vb['stride_bytes'],4))
    mid = auth[fid]['elements'][ai]['native_material_id']
    if d['draw'] in color:
        mid = color[d['draw']]['material']
        controls = color[d['draw']]['controls']
        if controls[5] != 0:
            no = np.ndarray((len(local),3),'<i2',raw,vb['data_file_offset']+20,(vb['stride_bytes'],2)).astype(float)
            no /= np.maximum(np.linalg.norm(no,axis=1,keepdims=True),1e-9)
            ab = np.abs(local.astype('<f4'))
            phase = np.float32(np.float32(ab[:,0]+ab[:,1])+ab[:,2])*np.float32(.1)
            phase = np.float32(phase-np.floor(phase))
            phase = np.uint32(np.float32(phase*np.float32(10)))
            world += (no@M[:3,:3])*(controls[5]*palette[phase,None])
    state = states.get(mid,{})
    tri = world[ix]
    e1,e2 = tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]
    for ri,(a,dr) in enumerate(rays):
        p = np.cross(np.broadcast_to(dr,e2.shape),e2)
        det = np.einsum('ij,ij->i',e1,p)
        valid = abs(det)>1e-10
        inv = np.zeros_like(det)
        inv[valid] = 1/det[valid]
        tv = a-tri[:,0]
        u = np.einsum('ij,ij->i',tv,p)*inv
        cr = np.cross(tv,e1)
        v = cr@dr*inv
        t = np.einsum('ij,ij->i',e2,cr)*inv
        ok = valid&(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)&(t>0)
        for k in np.flatnonzero(ok):
            bary = np.array([1-u[k]-v[k],u[k],v[k]])
            pos = bary@tri[k]
            cpos = vp@np.r_[pos,1]
            if not -1 <= cpos[2]/cpos[3] <= 1:
                continue
            uvs = uv[ix[k]].astype(float)
            value = bary@uvs
            clips = np.c_[tri[k],np.ones(3)]@vp.T
            screen = np.c_[(clips[:,0]/clips[:,3]+1)*width*.5,(1-clips[:,1]/clips[:,3])*height*.5]
            base = np.stack([screen[1]-screen[0],screen[2]-screen[0]],1)
            der = np.linalg.inv(base)
            st = der@(np.array(pixels[ri],float)+.5-screen[0])
            lam = np.r_[1-st.sum(),st]
            dl = np.vstack([-der.sum(0),der])
            iw = 1/clips[:,3]
            den,num = lam@iw,(lam*iw)@uvs
            grad = np.empty((2,2))
            for axis in range(2):
                grad[axis] = ((dl[:,axis]*iw)@uvs*den-num*(dl[:,axis]@iw))/(den*den)
            row = dict(draw=d['draw'],vs=d['vs'],pipeline=d['pipeline'],fab=fid,fab_name=option['name'],assembly=ai,native_material=mid,distance=float(t[k]),world=pos.tolist(),object_translation=M[3,:3].tolist(),uv=value.tolist(),uv_gradients=grad.tolist(),det=float(det[k]),triangle=int(k),pose_source_matched=d['pose_matched'],position_triangle=tri[k].tolist(),uv_triangle=uvs.tolist(),source_geometry=option['source'],alpha_test=state.get('source_alpha_test'),cull_mode=state.get('source_cull_mode'))
            coverage = 1.0
            cutoff = state.get('source_cutoff',0)
            if mid in [359202,419060,559590]:
                tid = 679 if mid == 359202 else 680
                row['alpha_sample'] = sample(tid,value,grad)
                row['alpha_texture'] = tid
                coverage = row['alpha_sample']['rgba'][1]
                cutoff = 100/255 if mid == 359202 else 128/255
                row['alpha_test'] = True
            elif mid == 489469:
                row['alpha_sample'] = sample(667,value,grad)
                coverage = row['alpha_sample']['rgba'][1]
            row['coverage'],row['cutoff'] = coverage,cutoff
            row['passes_alpha'] = not row['alpha_test'] or coverage >= cutoff
            row['culled_backface'] = state.get('source_cull_mode') == 2 and det[k] < 0
            hits[ri].append(row)

out = []
for pixel,items in zip(pixels,hits):
    items.sort(key=lambda v:v['distance'])
    covered = [h for h in items if h['passes_alpha'] and not h['culled_backface']]
    out.append(dict(pixel=pixel,first_covered_tree_hit=covered[0] if covered else None,hits=items))
    print('PIXEL',pixel,'NATIVE',None if not covered else {k:covered[0][k] for k in ['draw','fab','assembly','native_material','distance','coverage','pose_source_matched']})
report = dict(scope='Three rays against189 captured tree draws with byte-exact cached geometry. Original per-draw world matrices, actual leaf-material controls and captured leaf wind palette applied. Leaf alpha maps proven fully captured-exact; isotropic trilinear derivative sampler. Non-tree original occluders/post not replayed.',pixels=out)
(Q/'canopy-native-3pixel-raycast.json').write_text(json.dumps(report,indent=2,default=lambda x:x.item()))
