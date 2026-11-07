from pathlib import Path
import json,struct,sys,subprocess,hashlib
from PIL import Image
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');Q=Path(__file__).resolve().parent;G=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning');sys.path.insert(0,str(P/'work/v09-textures'));import keen_texture
plan=json.loads((Q/'material-texture-plan.json').read_text());need=plan['missing_textures'];lists={}
for arch,tag in [('DATA_0.pak','DATA'),('initial_0.pak','initial'),('patch_0.pak','patch')]:
 b=(P/f'outputs/{tag}-archive-list.txt').read_bytes();lists[arch]=set(x.strip() for x in b.decode('utf-16' if b[:2]==b'\xff\xfe' else 'utf-8-sig').splitlines())
O=Q/'extra-textures';O.mkdir(exist_ok=True);report=[]
for row in need:
 id=row['asset'];found=[]
 if id:
  for arch in ['patch_0.pak','initial_0.pak','DATA_0.pak']:
   names=[n for n in [f'{id}.dds']+[f'{id}_{i}.dds' for i in range(1,7)] if n in lists[arch]];folder=Q/'inputs'/arch;folder.mkdir(parents=True,exist_ok=True)
   todo=[n for n in names if not (P/'work/v20-inputs'/arch/n).exists() and not (folder/n).exists()]
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
 if not found:report.append(dict(**row,status='unavailable'));continue
 w,h,blocks,fmt,src,sha=max(found,key=lambda x:x[0]*x[1]);rgba=bytes(keen_texture.decode_blocks(blocks,w,h,fmt));assert len(rgba)==w*h*4;im=Image.frombytes('RGBA',(w,h),rgba);mips=[]
 while True:
  pix=im.tobytes();mips.append(struct.pack('<I',len(pix))+pix)
  if im.width==im.height==1:break
  im=im.resize((max(1,im.width//2),max(1,im.height//2)),Image.Resampling.BOX)
 blob=b'OATX'+struct.pack('<4I',0x8058,w,h,len(mips))+b''.join(mips);fn=f"native-{id}-{row['kind']}.bin";(O/fn).write_bytes(blob);report.append(dict(**row,status='ready',file=fn,width=w,height=h,mips=len(mips),bytes=len(blob),sha256=hashlib.sha256(blob).hexdigest(),source=src,source_sha256=sha,format='OATX RGBA8 decodedUNORM, generatedBOXmips, originalalpha preserved'))
 print(id,row['kind'],report[-1]['status'],flush=True)
(Q/'extra-texture-manifest.json').write_text(json.dumps(report,indent=2))
