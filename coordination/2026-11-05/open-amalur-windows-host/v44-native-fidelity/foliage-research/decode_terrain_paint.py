"""Static native-contract terrain paint linkage. Read assets; write only selected research folder."""
import argparse, collections, hashlib, json, math, struct, zlib
from pathlib import Path

def sha(b): return hashlib.sha256(b).hexdigest()

def parse_terrain(b):
    o=104
    def u():
        nonlocal o
        v=struct.unpack_from('<I',b,o)[0];o+=4;return v
    bitsets=[]
    for _ in range(struct.unpack_from('<I',b,100)[0]):
        at=o;n=u();occupied=u();o+=(n+7)//8;bitsets.append(dict(offset=at,bits=n,set_count=occupied))
    mesh_start=o;o+=73
    for _ in range(u()):
        for _ in range(u()):
            for _ in range(u()):
                for stride in (24,2,12):
                    count=u();o+=count*stride
                o+=28
            u();count=u();o+=count*4+24
    o+=28 # field +0x148 and first MultiEntryFile descriptor
    rle_start=o;n=u();flag=u();A=[]
    while len(A)<n:
        run=u()
        assert run<=n-len(A)
        if flag:
            A.extend(struct.unpack_from('<%dI'%run,b,o));o+=run*4
        else:A.extend([None]*run)
        flag=not flag
    descriptor_start=o
    descriptor=struct.unpack_from('<6I',b,o);o+=24
    arrays=[]
    for _ in range(2):
        at=o;levels=[]
        for _ in range(u()):
            n=u();at2=o
            values=struct.unpack_from('<%dI'%n,b,o);o+=n*4
            levels.append(dict(offset=at2,count=n,values=values))
        arrays.append(dict(offset=at,levels=levels))
    return dict(bitsets=bitsets,mesh_start=mesh_start,rle_start=rle_start,rle_count=len(A),rle_occupied=sum(v is not None for v in A),descriptor_offset=descriptor_start,descriptor=descriptor,height=arrays[0],paint=arrays[1],embedded_texture_start=o)

def entry(s,key,descriptor):
    version,offset_bits,offset_alignment,length_bits,length_alignment,index_bits=descriptor
    at=(key&((1<<offset_bits)-1))*offset_alignment
    segment=key>>(offset_bits+length_bits)&((1<<index_bits)-1)
    n=struct.unpack_from('<I',s,at)[0]
    sizes=struct.unpack_from('<%dI'%n,s,at+4)
    assert n==1 and segment==0
    payload=at+4
    raw,total,zero,raw2,comp=struct.unpack_from('<5I',s,payload)
    assert raw==raw2 and zero==0 and comp<=total<=comp+32
    d=zlib.decompress(s[payload+20:payload+20+comp])
    assert len(d)==raw
    return at,payload+20,d

def parse_height_chunk(d, finest_width=16):
    """d15490 contract; exact per-grid rectangles and material set array."""
    o=4;tiles=[]
    def u():
        nonlocal o
        v=struct.unpack_from('<I',d,o)[0];o+=4;return v
    for i in range(struct.unpack_from('<I',d)[0]):
        start=o;rect=struct.unpack_from('<8H',d,o);o+=64
        part_masks=[]
        for _ in range(2):
            masks=[]
            for _ in range(u()):
                bits=u();set_count=u();payload=d[o:o+(bits+7)//8];o+=len(payload)
                assert sum(v.bit_count() for v in payload)==set_count
                masks.append(dict(bits=bits,set_count=set_count,payload_hex=payload.hex()))
            part_masks.append(masks)
        flags=d[o];o+=1;material_sets=[]
        if not flags&2:
            n=u();material_sets=list(struct.unpack_from('<%dI'%n,d,o));o+=n*4
        n=u();height_offset=o;o+=n*2
        n=u();o+=n
        bits=u();set_count=u();payload=d[o:o+(bits+7)//8];o+=len(payload)
        vertex_state=dict(bits=bits,set_count=set_count,payload_hex=payload.hex())
        if rect[1]-rect[0]==finest_width:
            bits=u();u();o+=(bits+7)//8+8
            n=u();o+=n
        tiles.append(dict(index=i,offset=start,end=o,rect=rect[:4],render_rect=rect[4:],flags=flags,material_sets=material_sets,height_offset=height_offset,part_triangle_masks=part_masks[0],part_skirt_masks=part_masks[1],vertex_state=vertex_state))
    assert o==len(d),(o,len(d))
    return tiles

def parse_palette(b,symbols):
    ptr,count,sets_ptr,sets_count=struct.unpack_from('<4I',b,8)
    rows=[]
    for i in range(count):
        v=struct.unpack_from('<3I4f',b,ptr+i*28)
        rows.append(dict(index=i,offset=ptr+i*28,diffuse=v[0],normal=v[1],diffuse_name=symbols['texture'].get(str(v[0])),normal_name=symbols['texture'].get(str(v[1])),opaque_u32=v[2],uv_scale=v[3],opaque_float=v[4],specular_parameter1=v[5],specular_parameter2=v[6]))
    sets=[]
    for i in range(sets_count):
        color,ptr,n,zero=struct.unpack_from('<4I',b,sets_ptr+i*16)
        sets.append(dict(index=i,offset=sets_ptr+i*16,color=hex(color),row_indices=list(struct.unpack_from('<%dI'%n,b,ptr))))
    return dict(rows=rows,sets=sets)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path.home()/'Documents/Opem Amalur');ap.add_argument('--out',type=Path);a=ap.parse_args()
    out=a.out or a.root/'work/v43-scene-fidelity/terrain-research';out.mkdir(parents=True,exist_ok=True)
    bp=next((a.root/'work/v20-inputs').rglob('431658.terrain_bin'));sp=a.root/'work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin';b=bp.read_bytes();s=sp.read_bytes();T=parse_terrain(b)
    # Native MultiEntryFile metadata, not proximity, determines all record locations.
    assert T['descriptor']==(1,21,64,8,32768,3)
    paints=[]
    for l,L in enumerate(T['paint']['levels'][1:],1):
        side=math.isqrt(L['count']);assert side*side==L['count']
        for i,key in enumerate(L['values']):
            at,zat,d=entry(s,key,T['descriptor']);assert len(d)==66568 and struct.unpack_from('<I',d)[0]==16641
            paints.append(dict(level=l,x=i%side,y=i//side,side=side,tile_width=4096//side,key=key,key_hex=hex(key),field_offset=L['offset']+i*4,entry_offset=at,zlib_offset=zat,decoded_sha256=sha(d)))
    assert len(paints)==1344 and len({q['entry_offset'] for q in paints})==1344
    door=(1575.1,-62759.2,5152.1);origin=struct.unpack_from('<2f',b,40);scale=struct.unpack_from('<f',b,20)[0]
    uv=((door[0]-origin[0])/scale,(door[1]-origin[1])/scale)
    example=next(q.copy() for q in paints if q['level']==3 and q['x']==int(uv[0]/128) and q['y']==int(uv[1]/128))
    _,_,d=entry(s,example['key'],T['descriptor']);xy=(int(uv[0])%128,int(uv[1])%128);px=4+4*(xy[1]*129+xy[0]);example.update(world=door,map_coordinates=uv,local_pixel=xy,pixel_bytes=list(d[px:px+4]),pixel_u32=hex(struct.unpack_from('<I',d,px)[0]),pixel_decoded_offset=px)
    H=T['height']['levels'][0];hx=int(uv[0]/16);hy=int(uv[1]/16);hi=hy*257+hx;hk=H['values'][hi];hat,hzat,hd=entry(s,hk,T['descriptor'])
    example['height_tile']=dict(lod=0,x=hx,y=hy,index=hi,field_offset=H['offset']+hi*4,key=hk,key_hex=hex(hk),entry_offset=hat,zlib_offset=hzat,decoded_size=len(hd),header_I8H=struct.unpack_from('<I8H',hd),decoded_sha256=sha(hd))
    tiles=parse_height_chunk(hd);example['height_grid']=next(q for q in tiles if q['rect'][0]<=uv[0]<q['rect'][1] and q['rect'][2]<=uv[1]<q['rect'][3])
    pal=out/'325525.palettetmp_bxml'
    if pal.exists():
        palette=parse_palette(pal.read_bytes(),json.loads((a.root/'work/v20-inputs/symbols.json').read_text()))
        example['material_set']=palette['sets'][example['height_grid']['material_sets'][0]]
        example['materials']=[palette['rows'][q] for q in example['material_set']['row_indices']]
        (out/'palette-evidence.json').write_text(json.dumps(palette,indent=2))
    (out/'door-paint-129x129.u32').write_bytes(d[4:]);(out/'paint-manifest.json').write_text(json.dumps(paints,indent=2))
    summary={k:v for k,v in T.items() if k not in ['height','paint']};summary.update(sources=[dict(path=str(bp),bytes=len(b),sha256=sha(b)),dict(path=str(sp),bytes=len(s),sha256=sha(s))],height_levels=[dict(offset=q['offset'],count=q['count']) for q in T['height']['levels']],paint_levels=[dict(offset=q['offset'],count=q['count']) for q in T['paint']['levels']],paint_records_verified=len(paints),door_example=example)
    (out/'linkage-evidence.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
