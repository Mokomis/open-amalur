"""Non-destructive v0.34 package: coherent Dalentarth base + reviewed overlays."""
from pathlib import Path
import hashlib,json,shutil,subprocess,sys,zipfile,time
r=Path(__file__).resolve().parents[2];v=r/'work/v43-scene-fidelity';w=r/'work/v40-windows-host'
stage=r/'work/v43-apk';stage.mkdir(exist_ok=True);out=r/'outputs/scene-v43';out.mkdir(exist_ok=True)
base=r/'outputs/scene-v19/opem-amalur-scene-v0.33-arm64.apk'
apk=out/'open-amalur-v0.34-arm64.apk'
if apk.exists():raise RuntimeError('Preserve existing APK; use a new version/output name')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def run(cmd,name):
 t=time.monotonic();a=subprocess.run([str(x) for x in cmd],capture_output=True,timeout=300)
 (out/(name+'.log')).write_bytes(a.stdout+a.stderr)
 if a.returncode:raise RuntimeError(name+' failed '+str(a.returncode))
 return a.stdout.decode('utf-8',errors='replace')
receipt=json.loads((v/'final-renderer-build.json').read_text())
assert receipt['windows']==receipt['android']==0
for n,h in receipt['sources'].items():assert sha(r/'work/v19-host'/n)==h,n
lib=r/'work/v19-host/build-android-arm64/libopem_amalur_scene.so'
assert sha(lib)==receipt['android_library_sha256']
manifest=(r/'work/v19-host/AndroidManifest.xml').read_text().replace('versionCode="35"','versionCode="36"').replace('versionName="0.33.0"','versionName="0.34.0"').replace('android:label="Opem Amalur Scene"','android:label="Open Amalur"')
(stage/'AndroidManifest.xml').write_text(manifest,encoding='utf-8')
bt=r/'tools/android/sdk/android-15';java=r/'tools/jdk-21.0.13+9/bin/java.exe'
manifest_apk=stage/'manifest.apk'
run([bt/'aapt2.exe','link','-o',manifest_apk,'--manifest',stage/'AndroidManifest.xml','-I',r/'tools/android/sdk/android-35/android.jar','--min-sdk-version','26','--target-sdk-version','35'],'manifest')
world=set()
for f in ['work/v42-object-visuals/static-props-manifest.json','work/v42-object-visuals/visual-collision-manifest.json','work/v43-scene-fidelity/integrated-world-manifest.json']:
 world.update(json.loads((r/f).read_text())['files'])
world.add('post.bin')
overrides={'assets/world/'+n:w/'assets/world'/n for n in sorted(world)}
overrides['assets/actors/index.bin']=w/'assets/actors/index.bin'
overrides['lib/arm64-v8a/libopem_amalur_scene.so']=lib
records={n:{'bytes':p.stat().st_size,'sha256':sha(p)} for n,p in overrides.items()}
with zipfile.ZipFile(base) as z:
 sh=hashlib.sha256(z.read('assets/scene.bin')).hexdigest()
 assert ('AMALUR_SCENE_SHA256:STRING='+sh) in (r/'work/v19-host/build-android-arm64/CMakeCache.txt').read_text()
 assert sh.encode()+b'\0' in lib.read_bytes()
 base_names=set(z.namelist())
 assert 'assets/world/index.bin' in base_names
unsigned=stage/'unsigned.apk'
preserved=0
with zipfile.ZipFile(base) as src,zipfile.ZipFile(manifest_apk) as mz,zipfile.ZipFile(unsigned,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as dst:
 replacement={x.filename for x in mz.infolist()}
 for zi in src.infolist():
  if zi.filename in overrides or zi.filename in replacement or zi.filename.startswith('META-INF/'):continue
  with src.open(zi) as i,dst.open(zi,'w',force_zip64=True) as o:shutil.copyfileobj(i,o,1024*1024)
  preserved+=1
 for zi in mz.infolist():dst.writestr(zi,mz.read(zi))
 for n,p in overrides.items():dst.write(p,n)
aligned=stage/'aligned.apk'
run([bt/'zipalign.exe','-f','-P','16','4',unsigned,aligned],'align')
key=r/'tools/android/opem-scene-debug.keystore';assert key.exists()
run([java,'-jar',bt/'lib/apksigner.jar','sign','--ks',key,'--ks-key-alias','opem-scene-debug','--ks-pass','pass:android','--key-pass','pass:android','--v1-signing-enabled','false','--v2-signing-enabled','true','--v3-signing-enabled','true','--out',apk,aligned],'sign')
cert=run([java,'-jar',bt/'lib/apksigner.jar','verify','--verbose','--print-certs',apk],'verify')
oldcert=run([java,'-jar',bt/'lib/apksigner.jar','verify','--print-certs',base],'base-cert')
def digest(s):return next(x.split(':',1)[1].strip() for x in s.splitlines() if 'certificate SHA-256 digest:' in x)
assert digest(cert)==digest(oldcert)
run([bt/'zipalign.exe','-c','-P','16','4',apk],'alignment-verify')
run([bt/'aapt2.exe','dump','badging',apk],'badging')
with zipfile.ZipFile(apk) as z,zipfile.ZipFile(base) as bz:
 names=z.namelist();assert len(names)==len(set(names));assert z.testzip() is None
 for n,a in records.items():
  h=hashlib.sha256()
  with z.open(n) as s:
   for b in iter(lambda:s.read(4*1024*1024),b''):h.update(b)
  assert h.hexdigest()==a['sha256'],n
 # ZIP CRC/size equality for every preserved entry, then explicit hash the scene and ASTC sentinel.
 for n in set(names)&base_names-set(overrides)-replacement:
  assert (z.getinfo(n).CRC,z.getinfo(n).file_size)==(bz.getinfo(n).CRC,bz.getinfo(n).file_size),n
 for n in ['assets/scene.bin','assets/world/t0.bin']:
  if n in names and n in base_names:assert z.read(n)==bz.read(n)
 result={'apk':str(apk),'bytes':apk.stat().st_size,'sha256':sha(apk),'versionCode':36,'versionName':'0.34.0','package':'org.opemamalur.scene','signer_sha256':digest(cert),'base':str(base),'base_sha256':sha(base),'scene_sha256':sh,'overrides':records,'preserved_entries':preserved,'signed_payload_verified':True,'device_executed':False,'scope':'Recovered terrain paint in 18 cells, 267 added static visuals, visual collision, scoped native dot3 and captured Noon/post constants; authored blur and unsupported material families remain.'}
 (out/'android-apk-manifest.json').write_text(json.dumps(result,indent=2))
 print(json.dumps({k:a for k,a in result.items() if k!='overrides'},indent=2))
