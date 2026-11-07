from pathlib import Path
import json,struct,hashlib,collections
Q=Path(__file__).resolve().parent;R=Q.parent;P=json.loads((R/'water-pack.json').read_text());INFO={x['image']:x for x in json.loads((R/'image-provenance.json').read_text()) if x['aspect']==1};sha=lambda b:hashlib.sha256(b).hexdigest()
# Reuse only the reviewed decoder definition; do not import/execute the v1 pack writer.
source=(R/'make_pack.py').read_text();a=source.index('def decode(');z=source.index('\ntex=[]',a);exec(source[a:z])
v1=(R/'water-native.bin').read_bytes();magic,version,nt,nm=struct.unpack_from('<4s3I',v1);assert magic==b'OAWP' and version==1 and nt==12 and nm==8;off=16;v1_top={}
for _ in range(nt):
 id,faces,w,h,n=struct.unpack_from('<5I',v1,off);off+=20;v1_top[id]=v1[off:off+n];off+=n
old_tail=v1[off:];old_tail_start=off;pack=bytearray(struct.pack('<4s3I',b'OAWP',2,nt,nm));records=[];coverage=collections.Counter();padding=0
for tex in P['textures']:
 id=tex['id'];info=INFO[id];ci=info['create_info'];w0=ci['extent']['width'];h0=ci['extent']['height'];faces=ci['arrayLayers'];levels=ci['mipLevels'];assert len(info['level_sizes'])==levels;raw=(R/'resources'/f'image-{id}-aspect1.bin').read_bytes();assert sha(raw)==info['sha256'];mips=[];proof=[];mipoff=0;fmt=ci['format'];bc3=fmt=='VK_FORMAT_BC3_UNORM_BLOCK';assert bc3 or fmt=='VK_FORMAT_BC1_RGBA_UNORM_BLOCK'
 for lev,stored in enumerate(info['level_sizes']):
  w=max(1,w0>>lev);h=max(1,h0>>lev);facebytes=((w+3)//4)*((h+3)//4)*(16 if bc3 else 8);stride=((facebytes+511)//512)*512;assert stored==stride*faces,(id,lev,stored,stride,faces);rgba=[];face_proof=[]
  for face in range(faces):
   start=mipoff+face*facebytes;bc=raw[start:start+facebytes];assert len(bc)==facebytes;pixels=decode(bc,w,h,bc3);assert len(pixels)==w*h*4;rgba.append(pixels);face_proof.append(dict(face=face,source_offset=start,source_bc_bytes=facebytes,source_payload_stride=facebytes,ignored_padding_bytes=0,source_bc_sha256=sha(bc),rgba_bytes=len(pixels),rgba_sha256=sha(pixels)));coverage['subresources']+=1
  pixels=b''.join(rgba)
  if lev==0:assert pixels==v1_top[id],(id,'top mip changed')
  mips.append(struct.pack('<3I',w,h,len(pixels))+pixels);proof.append(dict(level=lev,width=w,height=h,source_level_offset=mipoff,source_level_stored_bytes=stored,source_level_tight_bytes=facebytes*faces,source_level_tail_padding_bytes=stored-facebytes*faces,rgba_bytes=len(pixels),faces=face_proof));mipoff+=stored;coverage['texture_levels']+=1;padding+=stored-facebytes*faces
 assert mipoff==len(raw);payload=b''.join(mips);texhead=struct.pack('<6I',id,faces,w0,h0,levels,sum(x['rgba_bytes'] for x in proof));pack+=texhead+payload;records.append(dict(image=id,format=fmt,faces=faces,width=w0,height=h0,mip_count=levels,maximum_gl_level=levels-1,source_image_init=info,levels=proof));coverage['textures']+=1;coverage['cubes' if faces==6 else '2d_textures']+=1
v2_tail_start=len(pack);pack+=old_tail;out=R/'water-native-mips.bin';out.write_bytes(pack)
# Parse resulting v2 texture records independently to catch pack framing/coverage errors.
o=16
for rec in records:
 id,faces,w0,h0,levels,total=struct.unpack_from('<6I',pack,o);o+=24;assert id==rec['image'];count=0
 for lev in range(levels):
  w,h,n=struct.unpack_from('<3I',pack,o);o+=12;assert w==max(1,w0>>lev) and h==max(1,h0>>lev) and n==w*h*faces*4;o+=n;count+=n
 assert count==total
assert o==v2_tail_start and pack[o:]==old_tail
meta=dict(version=2,file=out.name,bytes=len(pack),sha256=sha(pack),source_v1_sha256=sha(v1),source_v1_bytes=len(v1),v1_draw_payload_offset=old_tail_start,v2_draw_payload_offset=v2_tail_start,draw_payload_bytes=len(old_tail),draw_payload_sha256=sha(old_tail),draw_payload_identical=True,all_top_mips_identical=True,coverage=dict(coverage),ignored_capture_padding_bytes=padding,format='OAWP,u32version2,u32textureCount,u32drawCount; textures:<6I>id,faces,topW,topH,mipCount,totalRGBAbytes; then eachmip:<3I>w,h,RGBAbytes+face-majorRGBA; all v1 draw data unchanged',decoder='same reviewed v1 integer BC1/BC3 decoder; portableRGBA8 endpoint/interpolation rounding, no resampling or mipgeneration',textures=records);(Q/'water-mip-pack-manifest.json').write_text(json.dumps(meta,indent=2));print(json.dumps({k:meta[k] for k in ['bytes','sha256','coverage','ignored_capture_padding_bytes','draw_payload_identical','all_top_mips_identical']},indent=2))
