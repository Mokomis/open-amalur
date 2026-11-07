"""Stage two source-backed Dot3Alpha profiles and exact authored OATX chains."""
from pathlib import Path
from PIL import Image
import ast,hashlib,io,json,struct

P = Path.home()/'Documents/Opem Amalur'
Q = Path(__file__).resolve().parent
W = P/'work/v40-windows-host/assets/world'
O = Q/'candidate-materials'
O.mkdir(exist_ok=True)
S = json.loads((P/'work/v20-inputs/symbols.json').read_text())
# Import only the already-reviewed scalar decoder definitions, without executing
# the older staging script or writing into its output directory.
helper = P/'work/v44-native-fidelity/foliage-research/leaf-authored-auxiliary/build_authored_leaf_auxiliary.py'
tree = ast.parse(helper.read_text())
definitions = [n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['rgb565','ref_sample']]
exec(compile(ast.Module(body=definitions,type_ignores=[]),str(helper),'exec'))

def sha(b):
    return hashlib.sha256(b).hexdigest()

def find(name):
    return next((P/'work/v20-inputs'/a/name for a in ['patch_0.pak','initial_0.pak','DATA_0.pak'] if (P/'work/v20-inputs'/a/name).exists()),None)

jobs = [(343504,685),(357316,686),(357317,687),(343505,688),(1611838,689),(1611837,690),(365597,691),(4002,692)]
sizes = {}
for path in W.glob('t*.bin'):
    sizes.setdefault(path.stat().st_size,[]).append(path)
textures = []
for asset,reserved in jobs:
    source = find(f'{asset}_1.dds') or find(f'{asset}.dds')
    assert source is not None,asset
    b = source.read_bytes()
    assert b[16:20] == b'KEEN'
    w,h = struct.unpack_from('<2H',b,20)
    fmt = b[29]
    n = struct.unpack_from('<H',b,35)[0]
    assert fmt in [1,2,5]
    if fmt == 2:
        # This source default is a single opaque-black BC1-compatible block.
        # Selector2 with equal black endpoints has the same RGBA under both
        # opaque-RGB and one-bit-alpha BC1 interpretations; no enum guess leaks
        # into the staged result.
        assert (w,h,n,b[38:]) == (4,4,1,bytes.fromhex('00000000aaaaaaaa'))
    decode_fmt = 1 if fmt == 2 else fmt
    width,height = w,h
    off,levels,records = 38,[],[]
    for level in range(n):
        size = ((w+3)//4)*((h+3)//4)*(8 if decode_fmt == 1 else 16)
        blocks = b[off:off+size]
        assert len(blocks) == size
        header = [124,0x81007,h,w,size,0,1]+[0]*11+[32,4,int.from_bytes(b'DXT1' if decode_fmt == 1 else b'DXT5','little'),0,0,0,0,0]+[0x1000,0,0,0,0]
        rgba = Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*header)+blocks)).convert('RGBA').tobytes()
        points = {(0,0),(w-1,h-1),(w//2,h//2)}
        for i in range(128):
            points.add(((i*173+asset+level*7)%w,(i*359+asset//7+level*13)%h))
        for x,y in points:
            assert tuple(rgba[(y*w+x)*4:(y*w+x)*4+4]) == ref_sample(blocks,w,x,y,decode_fmt),(asset,level,x,y)
        levels.append(rgba)
        records.append(dict(level=level,width=w,height=h,source_offset=off,compressed_bytes=size,compressed_sha256=sha(blocks),rgba_sha256=sha(rgba),scalar_samples=len(points)))
        off += size
        w,h = max(1,w//2),max(1,h//2)
    assert off == len(b)
    blob = struct.pack('<4s4I',b'OATX',0x8058,width,height,n)+b''.join(struct.pack('<I',len(v))+v for v in levels)
    equal = [p for p in sizes.get(len(blob),[]) if p.read_bytes() == blob]
    tid = min(int(p.stem[1:]) for p in equal) if equal else reserved
    if not equal:
        (O/f't{tid}.bin').write_bytes(blob)
    at = 20
    for v in levels:
        size = struct.unpack_from('<I',blob,at)[0]
        at += 4
        assert blob[at:at+size] == v
        at += size
    assert at == len(blob)
    textures.append(dict(asset=asset,texture=tid,reserved_texture=reserved,reused_exact_existing_indices=[int(p.stem[1:]) for p in equal],source=str(source.relative_to(P)),source_sha256=sha(b),source_format=fmt,width=width,height=height,mips=n,output=None if equal else f'candidate-materials/t{tid}.bin',output_sha256=sha(blob),output_bytes=len(blob),levels=records))

byasset = {x['asset']:x['texture'] for x in textures}
profiles = []
for row,mid,cut,cull,assets in [(296,343630,150,2,[343504,343505,357317,357316]),(297,1611839,200,0,[1611838,4002,365597,1611837])]:
    source = find(f'{mid}.mat_bxml')
    b = source.read_bytes()
    assert struct.unpack_from('<4I',b,24) == (419915,1,cull,cut)
    # Source Dot3Alpha is the existing Dot3 material contract plus independent
    # raw-alpha GREEN coverage in depth and color passes.
    slots = [byasset[assets[0]],byasset[assets[1]],byasset[assets[2]],0xffffffff,0xffffffff,0xffffffff,byasset[assets[3]],0xffffffff]
    flags = 2 | (cut<<8) | 0x20000000 | (0x10000000 if cull == 2 else 0x08000000)
    mats = struct.pack('<7I',flags,*slots[:6])
    native = struct.pack('<9I12f',1,*slots,*([1.0]*4),1.0,20.0,0.0,0.0,*([1.0]*4))
    assert len(mats) == 28 and len(native) == 84
    (O/f'material-{row}.row28').write_bytes(mats)
    (O/f'native-material-{row}.row84').write_bytes(native)
    profiles.append(dict(material=row,native_material=mid,name=S['material'][str(mid)],family=1,shader_id=419915,shader='dot3alpha',source=str(source.relative_to(P)),source_sha256=sha(b),source_alpha_test=True,source_cull_mode=cull,source_cutoff_byte=cut,flags=flags,texture_indices=slots,color=[1,1,1,1],specular=[1,20,0,0],tiling=[1,1,1,1],materials_row_file=f'candidate-materials/material-{row}.row28',materials_row_sha256=sha(mats),native_row_file=f'candidate-materials/native-material-{row}.row84',native_row_sha256=sha(native)))

report = dict(status='isolated candidates only; no live bank/texture writes',material_count_after_root_merge=299,texture_count_required=max(x['texture'] for x in textures)+1,profiles=profiles,textures=textures,validation='Source BC1/BC3 every authored mip retained; independent scalar decode checks; complete serialized OATX payload identity; exact existing texture byte comparison before reuse.',limits=['Full source quality_1 authored chains, not a new captured residency claim.','Root merges rows296/297 against current banks and preserves all original rows.','Source alphaGREEN is independent of cull state;343630 isBACK,1611839NONE.','No material/tint tuning.'])
(Q/'region-material-stage-manifest.json').write_text(json.dumps(report,indent=2))
print(json.dumps(dict(profiles=[(x['material'],x['native_material'],x['flags']) for x in profiles],textures=[(x['asset'],x['texture'],x['reused_exact_existing_indices'],x['width'],x['height'],x['mips']) for x in textures],new_texture_bytes=sum(x['output_bytes'] for x in textures if x['output'])),indent=2))
