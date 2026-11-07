from pathlib import Path
import hashlib,io,json,struct
from PIL import Image
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');Q=P/'work/v44-native-fidelity/water-research/grass-mips';F=P/'work/v44-native-fidelity/foliage-research';W=Q/'world';W.mkdir(parents=True,exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
meta=json.loads((Q/'source-mip-hashes.json').read_text());decoded={};proof=[]
def decode(b,w,h,bc3):
 header=[124,0x81007,h,w,len(b),0,1]+[0]*11+[32,4,int.from_bytes(b'DXT5'if bc3 else b'DXT1','little'),0,0,0,0,0]+[0x1000,0,0,0,0]
 return Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*header)+b)).convert('RGBA')
for r in meta:
 if r['source_asset']is not None:
  source=P/'work/v20-inputs/initial_0.pak'/f"{r['source_asset']}_1.dds";raw=source.read_bytes();assert raw[16:20]==b'KEEN';assert struct.unpack_from('<2H',raw,20)==tuple(r['dimensions']);assert struct.unpack_from('<H',raw,35)[0]==r['mips'];o=38
 else:
  source=F/'native-captured-dissolve-noise-1816.raw';raw=source.read_bytes();assert sha(raw)==r['capture_sha256'];o=0
 images=[];levels=[]
 for lev in r['levels']:
  n=lev['bc_bytes'];bc=raw[o:o+n];assert sha(bc)==lev['bc_sha256'],(r['image'],lev['level'],'capture/source BC mismatch')
  im=decode(bc,lev['width'],lev['height'],'BC3'in r['format']);images.append(im)
  levels.append(dict(level=lev['level'],width=im.width,height=im.height,bc_sha256=sha(bc),rgba_sha256=sha(im.tobytes()),capture_exact_bc_match=True))
  o+=n if r['source_asset']is not None else lev['capture_stored_bytes']
 assert o==len(raw)
 decoded[r['image']]=images;proof.append(dict(image=r['image'],asset=r['source_asset'],path=str(source),source_sha256=sha(raw),levels=levels))
D=[im.copy()for im in decoded[15001]];A=decoded[15006];N=decoded[15020]
for d,a in zip(D,A):d.putalpha(a.getchannel('G'))
outputs=[]
for tid,ims,role in [(655,D,'343428 RGB + 344837 G in A'),(656,N,'3520 packed normal RGBA'),(657,A,'344837 raw alpha/specular RGBA'),(677,decoded[1816],'1816 captured dissolve noise RGBA')]:
 b=struct.pack('<4s4I',b'OATX',0x8058,*ims[0].size,len(ims))+b''.join(struct.pack('<I',len(im.tobytes()))+im.tobytes()for im in ims)
 old=P/'work/v44-native-fidelity/integrated-world'/f't{tid}.bin';current=old.read_bytes();same=b==current
 assert same,(tid,'integrated texture differs from exact authored chain')
 (W/f't{tid}.bin').write_bytes(b)
 outputs.append(dict(texture_id=tid,file=f'world/t{tid}.bin',role=role,bytes=len(b),sha256=sha(b),dimensions=list(ims[0].size),mips=len(ims),current_integrated_byte_identical=True))
alpha_equal=all(d.getchannel('A').tobytes()==a.getchannel('G').tobytes()for d,a in zip(D,A));assert alpha_equal
r=dict(images=proof,outputs=outputs,all_native_bc_mips_capture_exact=True,all_staged_textures_current_integrated_identical=True,merged_diffuse_alpha_equals_raw_alpha_green_at_every_authored_mip=alpha_equal,new_texture_ids_required=False,resampling=False,generated_mips=False,grass_shader_depth='module327 image33(15006).G * dissolve(noise1816.G) >= AlphaCutoff',current_shader_coverage='t655.A, copied per authored mip from rawt657.G; direct t657.G equivalent with matched samplers',native_sampler=dict(min='LINEAR_MIPMAP_LINEAR',mag='LINEAR',wrap_s='REPEAT',wrap_t='REPEAT',lod_bias=0,anisotropy=1,max_level_maps=8,max_level_noise=2),active_stream_sampler_discrepancy='oa_stream.c:137 unconditionally sets anisotropy4; captured native samplers disable anisotropy. Override1 for655/656/657/677 for parity.',decoder='Pillow BC1/BC3 to portable RGBA8 for each original mip; no image resize or mip generation. Source BC block payloads independently SHA-match captured resources for every authored level.')
(Q/'grass-mip-validation.json').write_text(json.dumps(r,indent=2));print(json.dumps(dict(outputs=outputs,all_capture_bc_mips_exact=True,all_current_integrated_identical=True,alpha_equal=alpha_equal),indent=2))
