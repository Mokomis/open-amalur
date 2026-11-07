from pathlib import Path
import struct,json,hashlib,io
from PIL import Image
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');Q=P/'work/v45-foliage-coverage/image-band-audit/left-bridge-structure/cart-material';W=Q/'world';W.mkdir(exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest();NONE=0xffffffff
images=[(697,425985,8630,'diffuse'),(698,426928,8615,'normal'),(699,426869,8620,'specular'),(700,426863,8625,'alpha/reflection mask')];native=json.loads((Q.parent/'native-subrange-evidence.json').read_text());infos={r['object']:r for r in native['resources']};outputs=[]
for tid,asset,image,role in images:
 cap=(Q.parent/f'image-{image}.bin').read_bytes();info=infos[image];assert sha(cap)==info['sha256'];bc3=image==8615;offset=0;levels=[];mips=[]
 for lev,stored in enumerate(info['level_sizes']):
  w=h=256>>lev;n=((w+3)//4)*((h+3)//4)*(16 if bc3 else 8);bc=cap[offset:offset+n];assert stored==((n+511)//512)*512
  header=[124,0x81007,h,w,n,0,1]+[0]*11+[32,4,int.from_bytes(b'DXT5'if bc3 else b'DXT1','little'),0,0,0,0,0]+[0x1000,0,0,0,0]
  rgba=Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*header)+bc)).convert('RGBA').tobytes();mips.append(struct.pack('<I',len(rgba))+rgba);levels.append(dict(level=lev,width=w,height=h,source_capture_offset=offset,bc_bytes=n,bc_sha256=sha(bc),rgba_sha256=sha(rgba)));offset+=stored
 assert offset==len(cap);found=[]
 for arch in ['patch_0.pak','initial_0.pak','DATA_0.pak']:
  for src in (P/'work/v20-inputs'/arch).glob(f'{asset}*.dds'):
   raw=src.read_bytes()
   if raw[16:20]!=b'KEEN' or raw[29]!=(5 if bc3 else 1):continue
   sw,sh=struct.unpack_from('<2H',raw,20);nm=struct.unpack_from('<H',raw,35)[0];o=38;seq=[]
   for lev in range(nm):
    w,h=max(1,sw>>lev),max(1,sh>>lev);n=((w+3)//4)*((h+3)//4)*(16 if bc3 else 8);seq.append((w,h,sha(raw[o:o+n]),o));o+=n
   assert o==len(raw)
   for start in range(nm-len(levels)+1):
    if all((a['width'],a['height'],a['bc_sha256'])==tuple(b[:3])for a,b in zip(levels,seq[start:])):found.append(dict(path=str(src),sha256=sha(raw),source_first_mip=start,width=sw,height=sh,mips=nm))
  if found:break
 assert found,(tid,asset,'source BC identity missing');blob=struct.pack('<4s4I',b'OATX',0x8058,256,256,7)+b''.join(mips);fn=f't{tid}.bin';(W/fn).write_bytes(blob);outputs.append(dict(texture_id=tid,asset=asset,captured_image=image,role=role,file='world/'+fn,sha256=sha(blob),bytes=len(blob),width=256,height=256,mips=7,source_matches=found,levels=levels,captured_all_mips_exact_source=True))
cb=struct.unpack_from('<16f',(Q/'capture-cb0-draw68274.bin').read_bytes());tint=list(cb[8:12]);spec=[cb[0],cb[1],cb[13],cb[14]];uv=[1.,1.,cb[7],cb[12]]
profile=struct.pack('<I8I12f',9,697,698,699,700,NONE,NONE,NONE,NONE,*tint,*spec,*uv);assert len(profile)==84;(Q/'native-material-row299.bin').write_bytes(profile);mat=struct.pack('<7I',0x10000000,697,698,699,700,NONE,NONE);(Q/'material-row299.bin').write_bytes(mat)
water=P/'work/v40-windows-host/assets/world/water-native.bin';pack=water.read_bytes();magic,version,nt,nm=struct.unpack_from('<4s3I',pack);assert magic==b'OAWP'and version==2;o=16;cube=None
for k in range(nt):
 start=o;id,faces,w0,h0,nlevels,total=struct.unpack_from('<6I',pack,o);o+=24;records=[]
 for lev in range(nlevels):
  w,h,n=struct.unpack_from('<3I',pack,o);o+=12;assert n==w*h*faces*4;records.append(dict(level=lev,width=w,height=h,rgba_offset=o,rgba_bytes=n,rgba_sha256=sha(pack[o:o+n])));o+=n
 if id==3594:cube=dict(image=id,faces=faces,width=w0,height=h0,mips=nlevels,texture_record_offset=start,rgba_bytes=total,levels=records)
assert cube and(cube['faces'],cube['width'],cube['mips'])==(6,128,6)
uniform=json.loads((Q/'capture-uniform-ranges.json').read_text());env=struct.unpack_from('<3f',(Q/'capture-cb1-draw68274.bin').read_bytes(),96);assert env==(1,1,1);assert(Q/'cart-environment.bin').read_bytes()==b'OARE001\0'+struct.pack('<3f',*env)
m=dict(native_material=426015,alias_material_row=299,material_count_after_merge=300,shader_family=9,native_shader_family='fresnelglassmetalprobe',draw=68274,vertex_shader=650,pixel_shader=651,source_DXBC='8af7b90f9cc700d2',material_profile_row84_sha256=sha(profile),MATS_row28_sha256=sha(mat),material_flags='0x10000000 force native BACK culling; opaque, no alpha discard',color=tint,specular=spec,uv=uv,texture_order=['diffuse697','normal698','specular699','alpha/reflectionmask700'],textures=outputs,environment=dict(file='cart-environment.bin',format='8B OARE001\\0 +3float32LE',source='captured CB1.environmentTint.rgb @96; buffer51,memory52,offset360992',value=env,sha256=sha((Q/'cart-environment.bin').read_bytes())),reflection=dict(asset='world/water-native.bin',format='OAWP version2; pertexture6u32header then eachmip3u32header+face-majorRGBA8; cube order+X,-X,+Y,-Y,+Z,-Z, rows unchanged',water_pack_sha256=sha(pack),water_pack_bytes=len(pack),cube=cube,loader='oa_cart_probe_open(assetManager,"world/water-native.bin",3594); binds sharedworld shader unit14; independentGLownership; do NOT edit water module'),captured_dynamic_luminance_shift=dict(value=.4375,source='CB4@252, not a material property'),required_sampler_state='2D linear/trilinear REPEAT anis1,bias0,maxLevel6; cube linear/trilinear CLAMP anis1,bias0,maxLevel5',ownership='new staging only; preserve material rows0..298; rebind only specificcart auxiliary run from row10 to299; do not globallychange row10 or water module')
(Q/'material-contract-and-merge-plan.json').write_text(json.dumps(m,indent=2));print(json.dumps({k:m[k]for k in ['color','specular','uv','environment','required_sampler_state']},indent=2));print('ready maps',[(r['texture_id'],r['asset'],r['sha256'])for r in outputs])
