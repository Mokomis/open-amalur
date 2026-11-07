"""Stage exact authored native leaf normal/alpha chains; no active-pack writes."""
from pathlib import Path
from PIL import Image
import json,struct,io,hashlib
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent;O=Q/'staged-assets';O.mkdir(exist_ok=True)
def sha(b):return hashlib.sha256(b).hexdigest()
def rgb565(v):
 r=(v>>11)&31;g=(v>>5)&63;b=v&31
 return ((r<<3)|(r>>2),(g<<2)|(g>>4),(b<<3)|(b>>2),255)
def ref_sample(blocks,w,x,y,fmt):
 size=8 if fmt==1 else 16;off=((y//4)*((w+3)//4)+x//4)*size;p=(y%4)*4+x%4
 co=off if fmt==1 else off+8;c0,c1,bits=struct.unpack_from('<HHI',blocks,co);a=rgb565(c0);b=rgb565(c1)
 if c0>c1 or fmt==5:
  cols=[a,b,tuple((2*a[k]+b[k])//3 for k in range(3))+(255,),tuple((a[k]+2*b[k])//3 for k in range(3))+(255,)]
 else:cols=[a,b,tuple((a[k]+b[k])//2 for k in range(3))+(255,),(0,0,0,0)]
 rgba=cols[(bits>>(2*p))&3]
 if fmt==5:
  a0,a1=blocks[off:off+2];ix=int.from_bytes(blocks[off+2:off+8],'little');alphas=[a0,a1]
  if a0>a1:alphas.extend(((7-i)*a0+i*a1)//7 for i in range(1,7))
  else:alphas.extend(((5-i)*a0+i*a1)//5 for i in range(1,5));alphas.extend([0,255])
  rgba=rgba[:3]+(alphas[(ix>>(3*p))&7],)
 return rgba
jobs=[(1451347,678,'normal-main','initial_0.pak/1451347.dds',[293],1),(343436,679,'alpha-main','DATA_0.pak/343436_1.dds',[293],2),(477449,680,'alpha-sapling','DATA_0.pak/477449_1.dds',[294,295],2),(457710,684,'normal-sapling','DATA_0.pak/457710_1.dds',[294,295],1)]
result=[]
for asset,tid,kind,relative,materials,slot in jobs:
 source=P/'work/v20-inputs'/relative;b=source.read_bytes();assert b[16:20]==b'KEEN';width,height=struct.unpack_from('<2H',b,20);fmt=b[29];nm=struct.unpack_from('<H',b,35)[0];assert fmt in [1,5]
 off=38;w=width;h=height;levels=[];records=[]
 for level in range(nm):
  count=((w+3)//4)*((h+3)//4)*(8 if fmt==1 else 16);blocks=b[off:off+count];assert len(blocks)==count;off+=count
  hdr=[124,0x81007,h,w,count,0,1]+[0]*11+[32,4,int.from_bytes(b'DXT1' if fmt==1 else b'DXT5','little'),0,0,0,0,0]+[0x1000,0,0,0,0]
  rgba=Image.open(io.BytesIO(b'DDS '+struct.pack('<31I',*hdr)+blocks)).convert('RGBA').tobytes();assert len(rgba)==w*h*4
  pts={(0,0),(w-1,h-1),(w//2,h//2),(w-1,0),(0,h-1)}
  for i in range(128):pts.add(((i*173+asset+level*7)%w,(i*359+asset//7+level*13)%h))
  samples=[]
  for x,y in sorted(pts):
   actual=tuple(rgba[(y*w+x)*4:(y*w+x)*4+4]);expected=ref_sample(blocks,w,x,y,fmt);assert actual==expected,(asset,level,x,y,actual,expected);samples.append(dict(x=x,y=y,rgba=actual))
  levels.append(rgba);records.append(dict(level=level,width=w,height=h,source_offset=off-count,compressed_bytes=count,compressed_sha256=sha(blocks),rgba_bytes=len(rgba),rgba_sha256=sha(rgba),independent_samples=len(samples),samples=samples));w=max(1,w//2);h=max(1,h//2)
 assert off==len(b)
 blob=struct.pack('<4s4I',b'OATX',0x8058,width,height,nm)+b''.join(struct.pack('<I',len(v))+v for v in levels);at=20
 for v in levels:
  n=struct.unpack_from('<I',blob,at)[0];at+=4;assert blob[at:at+n]==v;at+=n
 assert at==len(blob);(O/f't{tid}.bin').write_bytes(blob)
 oldtid=18 if tid==684 else tid;current=(P/'work/v40-windows-host/assets/world'/f't{oldtid}.bin').read_bytes();_,cw,ch,cn=struct.unpack_from('<4I',current,4);current_levels=[];at=20;tw=cw;th=ch
 for i in range(cn):
  n=struct.unpack_from('<I',current,at)[0];at+=4;v=current[at:at+n];at+=n;match=next((z for z in records if z['width']==tw and z['height']==th),None);current_levels.append(dict(level=i,width=tw,height=th,authored_source_level=match['level'] if match else None,rgba_bytes_equal_to_authored=bool(match and sha(v)==match['rgba_sha256'])));tw=max(1,tw//2);th=max(1,th//2)
 result.append(dict(asset=asset,kind=kind,texture=tid,old_texture=oldtid,materials=materials,slot=slot,operation='append' if tid==684 else 'same-ID native-only replacement',source=str(source.relative_to(P)),source_sha256=sha(b),source_format='BC1' if fmt==1 else 'BC3',width=width,height=height,mips=nm,last_mip=[records[-1]['width'],records[-1]['height']],format='OATX GL_RGBA8 UNORM; allRGBAchannels retained',output=f'staged-assets/t{tid}.bin',output_bytes=len(blob),output_sha256=sha(blob),current_width=cw,current_height=ch,current_mips=cn,current_authored_mip_comparison=current_levels,authored_levels=records))
manifest=dict(status='staged only, active pack unchanged',maps=result,texture_count_after_merge=685,material_changes=[dict(material=m,native_slot=1,materials_slot=1,old_texture=18,new_texture=684) for m in [294,295]],same_id_replacements=[678,679,680],preserve_global_texture18=True,transformations='DecodeeachsourceauthoredBCmipleveltoRGBA8;noresize,nogeneratedmips,nochannelmerge,nopremultiplication,nogammaconversion',coverage='RawalphaGREEN remainsnativecoverage;main100/255,saplings128/255',sampler='Native149 repeat/trilinear/minmaglinear/bias0/anisotropyoff;GLESanisotropy1',validation='Independent scalar BC1/BC3 sample checks atallmips; fullserializeddecodedRGBApayloadsreparsedexact; per-source/per-level/outputSHA256')
(Q/'authored-leaf-auxiliary-manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps([dict(asset=r['asset'],texture=r['texture'],dimensions=[r['width'],r['height']],mips=r['mips'],bytes=r['output_bytes'],sha256=r['output_sha256'],samples=sum(x['independent_samples'] for x in r['authored_levels'])) for r in result],indent=2))
