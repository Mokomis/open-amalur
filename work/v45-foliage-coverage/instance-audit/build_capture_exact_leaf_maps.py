"""Stage native capture resident-quality leaf maps, never mutate the live pack."""
from pathlib import Path
from PIL import Image
import hashlib, io, json, struct

P = Path.home() / 'Documents/Opem Amalur'
Q = Path(__file__).resolve().parent
O = Q / 'capture-exact-leaf-stage'
O.mkdir(exist_ok=True)
layouts = {x['image']: x for x in json.loads((Q/'all-native-leaf-image-layouts.json').read_text())}

def sha(b):
    return hashlib.sha256(b).hexdigest()

def rgb565(v):
    r, g, b = (v>>11)&31, (v>>5)&63, v&31
    return ((r<<3)|(r>>2), (g<<2)|(g>>4), (b<<3)|(b>>2), 255)

def sample(blocks, w, x, y, fmt):
    size = 8 if fmt == 1 else 16
    off = ((y//4)*((w+3)//4)+x//4)*size
    p = (y%4)*4+x%4
    co = off if fmt == 1 else off+8
    c0, c1, bits = struct.unpack_from('<HHI', blocks, co)
    a, b = rgb565(c0), rgb565(c1)
    if c0 > c1 or fmt == 5:
        cols = [a,b,tuple((2*a[k]+b[k])//3 for k in range(3))+(255,),tuple((a[k]+2*b[k])//3 for k in range(3))+(255,)]
    else:
        cols = [a,b,tuple((a[k]+b[k])//2 for k in range(3))+(255,),(0,0,0,0)]
    rgba = cols[(bits>>(2*p))&3]
    if fmt == 5:
        a0, a1 = blocks[off:off+2]
        ix = int.from_bytes(blocks[off+2:off+8], 'little')
        alphas = [a0,a1]
        if a0 > a1:
            alphas.extend(((7-i)*a0+i*a1)//7 for i in range(1,7))
        else:
            alphas.extend(((5-i)*a0+i*a1)//5 for i in range(1,5))
            alphas.extend([0,255])
        rgba = rgba[:3]+(alphas[(ix>>(3*p))&7],)
    return rgba

jobs = [
    (678,1451347,4647,'initial_0.pak/1451347.dds',[293],1),
    (679,343436,13908,'DATA_0.pak/343436_1.dds',[293],2),
    (680,477449,14150,'DATA_0.pak/477449_3.dds',[294,295],2),
    (681,343437,13901,'DATA_0.pak/343437_1.dds',[293],0),
    (682,457709,14145,'DATA_0.pak/457709_3.dds',[294],0),
    (683,566740,5267,'DATA_0.pak/566740_0.dds',[295],0),
    (684,457710,14155,'DATA_0.pak/457710_3.dds',[294,295],1),
]
receipt = []
for tid, asset, image, relative, materials, slot in jobs:
    source = P/'work/v20-inputs'/relative
    b = source.read_bytes()
    assert b[16:20] == b'KEEN'
    width, height = struct.unpack_from('<2H',b,20)
    fmt = b[29]
    nm = struct.unpack_from('<H',b,35)[0]
    assert fmt in [1,5]
    layout = layouts[image]
    assert (width,height,nm) == (layout['create_info']['extent']['width'],layout['create_info']['extent']['height'],len(layout['mip_sizes']))
    native = (Q/f'native-leaf-image-{image}.raw').read_bytes()
    native_off, source_off = 0,38
    w,h = width,height
    rgba_levels, records = [],[]
    for level, native_size in enumerate(layout['mip_sizes']):
        n = ((w+3)//4)*((h+3)//4)*(8 if fmt == 1 else 16)
        blocks = b[source_off:source_off+n]
        assert len(blocks) == n
        assert blocks == native[native_off:native_off+n], (tid,level,'native BC mismatch')
        header = [124,0x81007,h,w,n,0,1]+[0]*11+[32,4,int.from_bytes(b'DXT1' if fmt == 1 else b'DXT5','little'),0,0,0,0,0]+[0x1000,0,0,0,0]
        rgba = Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*header)+blocks)).convert('RGBA').tobytes()
        points = {(0,0),(w-1,h-1),(w//2,h//2)}
        for i in range(128):
            points.add(((i*173+asset+level*7)%w,(i*359+asset//7+level*13)%h))
        for x,y in points:
            actual = tuple(rgba[(y*w+x)*4:(y*w+x)*4+4])
            assert actual == sample(blocks,w,x,y,fmt), (tid,level,x,y)
        records.append(dict(level=level,width=w,height=h,native_offset=native_off,native_padded_bytes=native_size,source_offset=source_off,compressed_bytes=n,compressed_sha256=sha(blocks),captured_bytes_exact=True,rgba_sha256=sha(rgba),scalar_samples=len(points)))
        rgba_levels.append(rgba)
        native_off += native_size
        source_off += n
        w,h = max(1,w//2),max(1,h//2)
    assert native_off == len(native) and source_off == len(b)
    blob = struct.pack('<4s4I',b'OATX',0x8058,width,height,nm)+b''.join(struct.pack('<I',len(v))+v for v in rgba_levels)
    at = 20
    for v in rgba_levels:
        n = struct.unpack_from('<I',blob,at)[0]
        at += 4
        assert blob[at:at+n] == v
        at += n
    assert at == len(blob)
    current_path = P/'work/v40-windows-host/assets/world'/f't{tid}.bin'
    current = current_path.read_bytes()
    changed = blob != current
    if changed:
        (O/f't{tid}.bin').write_bytes(blob)
    receipt.append(dict(texture=tid,asset=asset,captured_image=image,source=str(source.relative_to(P)),source_sha256=sha(b),width=width,height=height,mips=nm,materials=materials,native_slot=slot,materials_slot=slot,operation='same-ID replacement' if changed else 'verified unchanged',output=f'capture-exact-leaf-stage/t{tid}.bin' if changed else None,output_sha256=sha(blob),current_sha256=sha(current),output_bytes=len(blob),levels=records))
manifest = dict(status='staged only; no live pack writes',maps=receipt,same_id_replacements=[r['texture'] for r in receipt if r['output']],texture_count_unchanged=685,material_table_changes=[],purpose='Reproduce actual original bridge capture resident-quality chains, independent of geometry LOD.',proof='Every source compressed mip byte equals the actual bound captured image after stripping only metadata-recorded per-level allocation padding. Independently sampled BC decode and complete OATX reparse.',sampling='Native leaf sampler149: repeat, trilinear, linear min/mag, bias0, anisotropy disabled. GLES anisotropy1.',coverage='Depth pass binding32 raw alpha image13908 for359202,14150 for419060+559590; GREEN cutoffs100/255 and128/255. Color pass binding33 diffuse and35 normal.',quality_warning='Files _0/_3/_4 are independently authored quality chains; do not replace by tails of _1. This capture used566740_0 (identical_4),457709_3,477449_3,457710_3. Normal view dynamic residency policy remains separate.',transformations=['BC1/BC3 decode toRGBA8 UNORM only','No resizing','No generated mips','No channel merge','No gamma conversion','No changes to global legacy textures0/17/18/22'])
(Q/'capture-exact-leaf-stage-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps([dict(texture=x['texture'],image=x['captured_image'],size=[x['width'],x['height']],mips=x['mips'],operation=x['operation']) for x in receipt],indent=2))
