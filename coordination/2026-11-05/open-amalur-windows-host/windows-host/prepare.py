"""Prepare private Windows dependencies/assets without changing the Android tree."""
from pathlib import Path
import shutil,hashlib,json,zipfile,re,struct
w=Path(__file__).resolve().parent;r=w.parents[1];h=r/'work/v19-host'
dep=w/'dependencies';dep.mkdir(exist_ok=True)
ndk=r/'tools/android/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/sysroot/usr/include'
for name in ['EGL','GLES2','GLES3','KHR']:
 shutil.copytree(ndk/name,dep/'include'/name,dirs_exist_ok=True)
shutil.copy2(ndk/'android/keycodes.h',w/'include/android/keycodes.h')
angle=Path.home()/'AppData/Local/Programs/Daggerfall Online'
receipts={}
for name in ['libEGL.dll','libGLESv2.dll']:
 p=angle/name
 b=p.read_bytes();pe=struct.unpack_from('<I',b,0x3c)[0]
 assert struct.unpack_from('<H',b,pe+4)[0]==0x8664,'Need x64 ANGLE'
 shutil.copy2(p,dep/name);receipts[name]={'source':str(p),'sha256':hashlib.sha256(b).hexdigest()}
# Generate import libraries from API names actually used. Implementations remain in copied ANGLE DLLs.
text='\n'.join(p.read_text(errors='replace') for p in list(h.glob('*.c'))+list((r/'work/v09-textures').glob('*.c')))
for dll,pattern,extra in [('libGLESv2',r'\bgl[A-Z]\w*(?=\s*\()', ['glReadPixels','glGetString','glGetError','glFinish']),('libEGL',r'\begl[A-Z]\w*(?=\s*\()',[])]:
 names=sorted(set(re.findall(pattern,text)+extra))
 (dep/(dll+'.def')).write_text('LIBRARY '+dll+'\nEXPORTS\n'+'\n'.join(names)+'\n')
# Use the preserved Dalentarth APK as the complete, coherent content snapshot.
apk=r/'outputs/scene-v19/opem-amalur-scene-v0.33-arm64.apk'
assets=w/'assets'
if not assets.exists():
 assets.mkdir()
 with zipfile.ZipFile(apk) as z:
  for member in z.infolist():
   if member.filename.startswith('assets/') and not member.is_dir():
    rel=Path(member.filename).relative_to('assets');assert '..' not in rel.parts
    p=assets/rel;p.parent.mkdir(parents=True,exist_ok=True)
    with z.open(member) as src,p.open('wb') as dst:shutil.copyfileobj(src,dst)
# A marker is created only after complete extraction; an interrupted run must not pass.
assert (assets/'world/index.bin').exists() and (assets/'scene.bin').exists()
receipts['assets']={'apk':str(apk),'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'scene_sha256':hashlib.sha256((assets/'scene.bin').read_bytes()).hexdigest()}
(dep/'receipt.json').write_text(json.dumps(receipts,indent=2)+'\n')
# Event classification logic is shared verbatim; only OS inventory enumeration is replaced.
s=(h/'android_input_probe.c').read_text();s=s[:s.index('int opem_android_inventory_read(')]
s+='''int opem_android_inventory_read(JNIEnv *env,opem_android_inventory *out){(void)env;memset(out,0,sizeof(*out));out->count=2;out->devices[0].id=1;out->devices[0].sources=AINPUT_SOURCE_KEYBOARD;out->devices[1].id=2;out->devices[1].sources=AINPUT_SOURCE_MOUSE;return 1;}\n'''
(w/'desktop_input_probe.c').write_text(s)
print(json.dumps(receipts,indent=2))
