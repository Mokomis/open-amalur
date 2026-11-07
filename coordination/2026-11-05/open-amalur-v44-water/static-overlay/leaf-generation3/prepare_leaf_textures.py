from pathlib import Path
import json,struct,sys,subprocess,hashlib
from PIL import Image
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');Q=Path(__file__).resolve().parent;F=P/'work/v44-native-fidelity/foliage-research';G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning');BASE=P/'work/v40-windows-host/assets/world';sys.path.insert(0,str(P/'work/v09-textures'));import keen_texture
meta=json.loads((P/'work/v22-stress/zone-dal/zone_materials.json').read_text());s=(P/'work/v20-char/build_textures.py').read_text();s=s[s.index('tex_keys, tex_index'):s.index('print("materials"')];s=s.replace('CUTOFFS.get(str(len(rows)), 50)','50').replace('CUTOFFS.get(str(len(rows)), 128)','128');exec(s)
mb=(BASE/'materials.bin').read_bytes();assert struct.unpack_from('<I',mb)[0]==263
for i,row in enumerate(rows):
 actual=struct.unpack_from('<7I',mb,4+i*28)
 for e,g in zip(row[1:],actual[1:]):assert e==g or g==0xffffffff
listing={}
for arch,tag in [('DATA_0.pak','DATA'),('initial_0.pak','initial'),('patch_0.pak','patch')]:
 b=(P/f'outputs/{tag}-archive-list.txt').read_bytes();listing[arch]=set(x.strip() for x in b.decode('utf-16' if b[:2]==b'\xff\xfe' else 'utf-8-sig').splitlines())
O=Q/'textures';O.mkdir(exist_ok=True);generated={};nextid=678

def ready(tid,kind):
 global nextid
 existing=tex_index.get((tid,0,kind))
 if existing is not None and (BASE/f't{existing}.bin').exists():return existing
 if (tid,kind) in generated:return generated[(tid,kind)]['texture_index']
 found=[]
 for arch in ['patch_0.pak','initial_0.pak','DATA_0.pak']:
  names=[n for n in [f'{tid}.dds']+[f'{tid}_{i}.dds' for i in range(1,7)] if n in listing[arch]];folder=Q/'inputs'/arch;folder.mkdir(parents=True,exist_ok=True);todo=[n for n in names if not (P/'work/v20-inputs'/arch/n).exists() and not (folder/n).exists()]
  if todo:subprocess.run([str(G/'modding/pakfileunpacker.exe'),str(G/'data'/arch),'unpack',str(folder),*todo],cwd=G/'modding',capture_output=True,timeout=120,check=True)
  for n in names:
   f=P/'work/v20-inputs'/arch/n
   if not f.exists():f=folder/n
   if not f.exists():continue
   b=f.read_bytes()
   if b[16:20]!=b'KEEN' or b[29] not in [1,5]:continue
   w,h=struct.unpack_from('<HH',b,20);fmt=b[29];levels=struct.unpack_from('<H',b,35)[0];off=38
   for level in range(levels):
    size=((w+3)//4)*((h+3)//4)*(8 if fmt==1 else 16)
    if off+size>len(b):break
    if max(w,h)<=1024:found.append((w,h,b[off:off+size],fmt,str(f.relative_to(P)),hashlib.sha256(b).hexdigest()));break
    off+=size;w=max(1,w//2);h=max(1,h//2)
  if found:break
 assert found,(tid,kind)
 w,h,blocks,fmt,src,sha=max(found,key=lambda x:x[0]*x[1]);rgba=bytes(keen_texture.decode_blocks(blocks,w,h,fmt));assert len(rgba)==w*h*4;im=Image.frombytes('RGBA',(w,h),rgba);mips=[]
 while True:
  pix=im.tobytes();mips.append(struct.pack('<I',len(pix))+pix)
  if im.width==im.height==1:break
  im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.BOX)
 blob=b'OATX'+struct.pack('<4I',0x8058,w,h,len(mips))+b''.join(mips);idx=nextid;nextid+=1;fn=f't{idx}.bin';(O/fn).write_bytes(blob);generated[(tid,kind)]=dict(asset=tid,kind=kind,texture_index=idx,file=fn,width=w,height=h,mips=len(mips),bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),source=src,source_sha256=sha,alpha_policy='original RGBA preserved; native alpha reads G',mip_policy='source top at most1024; generatedBOX lower mips');return idx
profiles=json.loads((F/'native-leaf-material-profiles.json').read_text());out=[]
for m in profiles['rows']:
 tx={slot:id for id,slot in m['textures']};diffuse=tex_index.get((tx[0],tx[1],'d'));assert diffuse is not None and (BASE/f't{diffuse}.bin').exists(),m['native_material'];normal=ready(tx[3],'n');alpha=ready(tx[1],'mask');out.append(dict(material=m['material'],native_material=m['native_material'],texture_indices=[diffuse,normal,alpha]+[0xffffffff]*5,source_textures=tx,parameters=m['parameters'],alpha_reference_u8=m['alpha_reference_u8'],source=m['source'],source_sha256=m['source_sha256']))
receipt=dict(profiles=out,generated_textures=list(generated.values()),texture_count=nextid,reserved_noise_index=677,known_legacy_mapping_verified_rows=len(rows),existing_diffuse_policy='reuse exact original(asset,alpha,kind=d) build key; shader lit path ignores diffuse.a and depth reads dedicated original alphaMap.G');(Q/'leaf-textures-and-profiles.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
