"""Build isolated data proposal. No geometry, packs or renderer are changed."""
import argparse, collections, hashlib, json, math, struct, zlib
from pathlib import Path
from decode_terrain_paint import parse_terrain,entry,parse_height_chunk,parse_palette

def png_rgba(path,width,height,rgba):
    def chunk(k,b):return struct.pack('>I',len(b))+k+b+struct.pack('>I',zlib.crc32(k+b)&0xffffffff)
    co=zlib.compressobj(8);parts=[]
    for y in range(height):parts.append(co.compress(b'\0'+rgba[y*width*4:(y+1)*width*4]))
    parts.append(co.flush())
    path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',b''.join(parts))+chunk(b'IEND',b''))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path.home()/'Documents/Opem Amalur');ap.add_argument('--out',type=Path);a=ap.parse_args();out=a.out or a.root/'work/v43-scene-fidelity/terrain-research/proposal';out.mkdir(parents=True,exist_ok=True)
    b=next((a.root/'work/v20-inputs').rglob('431658.terrain_bin')).read_bytes();s=(a.root/'work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin').read_bytes();T=parse_terrain(b);L=T['paint']['levels'][3];N=4097;A=bytearray(N*N*4);maps=[]
    for i,k in enumerate(L['values']):
        _,_,d=entry(s,k,T['descriptor']);maps.append(d[4:]);tx=i%32;ty=i//32
        # Half-open tile ownership, except outermost +1 edge. Incoming right/top
        # tile owns shared seam sample; all original overlaps are checked below.
        for y in range(129 if ty==31 else 128):
            dest=((ty*128+y)*N+tx*128)*4;width=129 if tx==31 else 128
            A[dest:dest+width*4]=d[4+y*129*4:4+(y*129+width)*4]
    seam_x=seam_y=0
    for ty in range(32):
        for tx in range(32):
            q=maps[ty*32+tx]
            if tx<31:
                r=maps[ty*32+tx+1]
                seam_x+=sum(q[(y*129+128)*4:(y*129+129)*4]!=r[y*129*4:y*129*4+4] for y in range(129))
            if ty<31:
                r=maps[(ty+1)*32+tx]
                seam_y+=sum(q[(128*129+x)*4:(128*129+x+1)*4]!=r[x*4:x*4+4] for x in range(129))
    png_rgba(out/'terrain-431658-paint-linear-rgba.png',N,N,A)
    # Record exact grids around the shop, rather than claiming native bitset-to-
    # triangle semantics for multi-part tiles. Parent can preserve geometry and
    # attach exact source memberships in a separate reviewed stage.
    roi=(1960,2200,680,920);keys=set();H=T['height']['levels'][0]
    for gy in range(roi[2]//16,roi[3]//16+1):
        for gx in range(roi[0]//16,roi[1]//16+1):keys.add(H['values'][gy*257+gx])
    grids=[];empty=0
    for k in keys:
        at=(k&0x1fffff)*64
        if struct.unpack_from('<I',s,at+4)[0]==4:empty+=1;continue
        _,_,d=entry(s,k,T['descriptor'])
        for q in parse_height_chunk(d):
            x0,x1,y0,y1=q['rect']
            if x0<roi[1] and x1>roi[0] and y0<roi[3] and y1>roi[2]:
                q.update(source_key=hex(k),source_stream_offset=at);grids.append(q)
    # Native ceae80 uses 512 per-part triangle bits and a vertex-state
    # diagonal decision. Preserve exact boundaries as per-fragment selector.
    bounds=(min(g['rect'][0] for g in grids),max(g['rect'][1] for g in grids),min(g['rect'][2] for g in grids),max(g['rect'][3] for g in grids));W=bounds[1]-bounds[0];HH=bounds[3]-bounds[2];selector=bytearray([255])*(W*HH);owners=collections.Counter();overlaps=0
    def bit(data,i):return bool(data[i>>3]&(1<<(i&7)))
    for g in grids:
        x0,x1,y0,y1=g['rect'];assert x1-x0==16 and y1-y0==16
        masks=[bytes.fromhex(m['payload_hex']) for m in g['part_triangle_masks']];ids=g['material_sets'];assert len(masks)==len(ids)
        state=bytes.fromhex(g['vertex_state']['payload_hex']);assert g['vertex_state']['bits']==361
        for y in range(16):
            for x in range(16):
                picked=[]
                for tri in range(2):
                    matches=[ids[j] for j,m in enumerate(masks) if bit(m,(y*16+x)*2+tri)]
                    if len(matches)>1:overlaps+=1
                    picked.append(matches[0] if len(matches)==1 else 7)
                    owners[len(matches)]+=1
                alternate=not(bit(state,(y+1)*19+x+1) and bit(state,(y+2)*19+x+2))
                selector[(y0+y-bounds[2])*W+x0+x-bounds[0]]=picked[0]|(picked[1]<<3)|(int(alternate)<<6)
    assert overlaps==0
    (out/'reference-material-selector.r8ui').write_bytes(selector)
    selector_info=dict(file='reference-material-selector.r8ui',format='R8UI, nearest fetch',width=W,height=HH,map_bounds=bounds,world_origin=[bounds[0]*50-102425,bounds[2]*50-102425],world_units_per_texel=50,byte_layout='bits0..2 primary triangle material-set ID; bits3..5 second triangle material-set ID; bit6 alternate diagonal; ID7 means no owner',shader_decode='q=floor(mapXY); f=fract(mapXY); alt=(byte&64)!=0; tri=alt ? (f.x+f.y>1) : (f.y>f.x); set=(byte>>(tri*3))&7',native_sources=['00ceae80','VA0173e014=[0,1,2,0,2,3]','VA0173dffc=[3,0,1,3,1,2]'],triangle_owner_count_histogram=dict(owners),overlapping_triangle_owners=overlaps,sha256=hashlib.sha256(selector).hexdigest())
    (out/'reference-material-selector.json').write_text(json.dumps(selector_info,indent=2))
    palette_path=a.root/'work/v43-scene-fidelity/terrain-research/325525.palettetmp_bxml';P=parse_palette(palette_path.read_bytes(),json.loads((a.root/'work/v20-inputs/symbols.json').read_text()))
    materials=[]
    for q in P['sets']:
        rows=q['row_indices'];materials.append(dict(index=q['index'],rows=rows,diffuse_ids=[P['rows'][r]['diffuse'] for r in rows],normal_ids=[P['rows'][r]['normal'] for r in rows],map_uv_scales=[P['rows'][r]['uv_scale']*.5 for r in rows],world_uv_scales=[P['rows'][r]['uv_scale']/100 for r in rows]))
    (out/'native-material-grid-reference.json').write_text(json.dumps(dict(region_map_bounds=roi,grids=grids,materials=materials,palette=P),indent=2))
    duv=(2080,793);at=(duv[1]*N+duv[0])*4
    metadata=dict(terrain_id=431658,world_origin=[-102425,-102425],world_units_per_map_unit=50,paint_atlas=dict(file='terrain-431658-paint-linear-rgba.png',width=N,height=N,color_space='linear UNORM',channels='RGBA',world_to_map='(worldXY - worldOrigin)/50',normalized_uv='(mapXY+0.5)/4097',row_direction='increasing source mapY; no implicit vertical flip',sha256_rgba=hashlib.sha256(A).hexdigest(),neighbor_edge_pixel_mismatches=dict(horizontal=seam_x,vertical=seam_y)),door_floor_sample=dict(map_pixel=duv,rgba=list(A[at:at+4]),expected=[0,255,0,255]),reference_grids=dict(count=len(grids),single_material_set=sum(len(g['material_sets'])==1 for g in grids),multiple_material_sets=sum(len(g['material_sets'])>1 for g in grids),empty_descriptors=empty),geometry_changed=False,material_selector=selector_info,texture_alpha_policy='Preserve original diffuse alpha. It is shader height-blend input; old opaque-forcing decoding is unsuitable.',limits=['Global atlas drops duplicated internal border samples; mismatch audit must be reviewed before rendering.','Reference material selector recovers native per-triangle membership; renderer may duplicate ground draws per set and discard fragments whose selector differs.','No draw regrouping was applied; selector method avoids moving/splitting existing geometry. Geometry-height differences remain separate.','No texture files are decoded or copied here; eight IDs and exact UV scales per material set are emitted.','No runtime/visual parity established.'])
    assert metadata['door_floor_sample']['rgba']==[0,255,0,255]
    (out/'proposal.json').write_text(json.dumps(metadata,indent=2));print(json.dumps(metadata,indent=2))
if __name__=='__main__':main()
