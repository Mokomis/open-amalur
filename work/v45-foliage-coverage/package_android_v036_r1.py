"""One batched signed update; reuse unchanged compressed parent APK records."""
from pathlib import Path
import copy,hashlib,json,subprocess,time,zipfile,zlib,concurrent.futures,re
P=Path(__file__).resolve().parents[2];V=P/'work/v45-foliage-coverage';ST=P/'work/v45-apk-r1';OUT=P/'outputs/scene-v45-r1';OUT.mkdir(exist_ok=True);ST.mkdir(exist_ok=True)
BASE=P/'work/v44-apk-r4/unsigned.apk';APK=OUT/'open-amalur-v0.36-r1-arm64.apk';assert not APK.exists();ASSETS=P/'work/v40-windows-host/assets';LIB=P/'work/v19-host/build-android-arm64/libopem_amalur_scene.so';LIBNAME='lib/arm64-v8a/libopem_amalur_scene.so'
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(4194304),b''):h.update(b)
 return h.hexdigest()
def run(argv,label):
 r=subprocess.run([str(x) for x in argv],capture_output=True,timeout=300);(OUT/(label+'.log')).write_bytes(r.stdout+r.stderr);assert r.returncode==0,(label,r.returncode);return r.stdout.decode(errors='replace')
receipt=json.loads((V/'final-renderer-build.json').read_text());assert all(receipt[k]['exit']==0 for k in ['windows','android']);assert sha(LIB)==receipt['android_library_sha256']
for name,h in receipt['sources'].items():assert sha(P/'work/v19-host'/name)==h,name
for name,h in receipt['recipes'].items():assert sha(P/name)==h,name
started=time.monotonic();changed={LIBNAME:LIB};removed=[];worldmeta=[]
# CRC/size compare all prepared world files, so a correction cannot be omitted
# simply because it was absent from a hand-maintained override list.
with zipfile.ZipFile(BASE) as src:
 entries={x.filename:x for x in src.infolist()};assert len(entries)==len(src.infolist())
 def crc_file(path):
  crc=0
  with path.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):crc=zlib.crc32(b,crc)
  name='assets/'+path.relative_to(ASSETS).as_posix();zi=entries.get(name);n=path.stat().st_size
  return name,path,n,crc&0xffffffff,zi
 # Preserve prior Android texture codec/residency below680; Windows uses separate RGBA copies.
 files=sorted(x for x in ASSETS.rglob('*') if x.is_file() and not (x.parent.name=='world' and re.fullmatch(r't[0-9]+\.bin',x.name) and int(x.stem[1:])<680))
 with concurrent.futures.ThreadPoolExecutor(4) as ex:
  for name,path,n,crc,zi in ex.map(crc_file,files):
   if zi is None or zi.file_size!=n or zi.CRC!=crc:changed[name]=path;worldmeta.append({'name':name,'bytes':n,'crc32':crc,'sha256':sha(path),'new':zi is None})
 for name in entries:
  if name.startswith('assets/') and not name.endswith('/') and not (ASSETS/name[len('assets/'):]).exists():removed.append(name)
 assert not removed,removed
with zipfile.ZipFile(ST/'manifest.apk') as mz:manifest_payloads={x.filename:mz.read(x) for x in mz.infolist() if not x.filename.startswith('META-INF/')}
assert 'AndroidManifest.xml' in manifest_payloads
skip=set(changed)|set(manifest_payloads);unsigned=ST/'unsigned.apk';copied=0
with zipfile.ZipFile(BASE) as src,zipfile.ZipFile(unsigned,'w',allowZip64=True) as dst:
 infos=sorted(src.infolist(),key=lambda x:x.header_offset)
 for j,zi in enumerate(infos):
  if zi.filename in skip or zi.filename.startswith('META-INF/'):continue
  end=infos[j+1].header_offset if j+1<len(infos) else src.start_dir;assert end>zi.header_offset
  nz=copy.copy(zi);nz.header_offset=dst.fp.tell();src.fp.seek(zi.header_offset);remain=end-zi.header_offset
  while remain:
   data=src.fp.read(min(4194304,remain));assert data;dst.fp.write(data);remain-=len(data)
  dst.filelist.append(nz);dst.NameToInfo[nz.filename]=nz;copied+=1
 dst.start_dir=dst.fp.tell();dst._didModify=True;dst.comment=src.comment
 for name,path in sorted(changed.items()):dst.write(path,name,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
 for name,data in manifest_payloads.items():dst.writestr(name,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=6)
with zipfile.ZipFile(BASE) as src,zipfile.ZipFile(unsigned) as z:
 assert len(z.infolist())==len({x.filename for x in z.infolist()});assert z.testzip() is None;assert z.read(LIBNAME)==LIB.read_bytes()
 for zi in src.infolist():
  if zi.filename not in skip and not zi.filename.startswith('META-INF/'):
   q=z.getinfo(zi.filename);assert(zi.CRC,zi.file_size,zi.compress_size,zi.compress_type)==(q.CRC,q.file_size,q.compress_size,q.compress_type),zi.filename
 for name,path in changed.items():assert hashlib.sha256(z.read(name)).hexdigest()==sha(path),name
bt=P/'tools/android/sdk/android-15';java=P/'tools/jdk-21.0.13+9/bin/java.exe';aligned=ST/'aligned.apk';run([bt/'zipalign.exe','-f','-P','16','4',unsigned,aligned],'align');key=P/'tools/android/opem-scene-debug.keystore';assert key.exists()
run([java,'-jar',bt/'lib/apksigner.jar','sign','--ks',key,'--ks-key-alias','opem-scene-debug','--ks-pass','pass:android','--key-pass','pass:android','--v1-signing-enabled','false','--v2-signing-enabled','true','--v3-signing-enabled','true','--out',APK,aligned],'sign')
cert=run([java,'-jar',bt/'lib/apksigner.jar','verify','--verbose','--print-certs',APK],'verify');signer=next(x.split(':',1)[1].strip() for x in cert.splitlines() if 'certificate SHA-256 digest:' in x);prior=json.loads((P/'outputs/scene-v44-r4/android-apk-manifest.json').read_text());assert signer==prior['signer_sha256']
run([bt/'zipalign.exe','-c','-P','16','4',APK],'alignment-verify');badging=run([bt/'aapt2.exe','dump','badging',APK],'badging');assert "versionCode='38'" in badging and "versionName='0.36.0'" in badging
r={'apk':str(APK),'bytes':APK.stat().st_size,'sha256':sha(APK),'package':'org.opemamalur.scene','version_name':'0.36.0','version_code':38,'signer_sha256':signer,'parent':str(BASE),'source_receipt':str(V/'final-renderer-build.json'),'raw_compressed_entries_reused':copied,'changed_asset_files':worldmeta,'native_library_sha256':sha(LIB),'package_seconds':time.monotonic()-started,'device_executed':False,'android_texture_policy':'Preserve parent t0..679 codec/residency; explicit authored corrections680/682/683/684 and new685+ only','private_key_copied':False,'all_zip_CRC_checked':True,'all_changed_payload_sha_checked':True}
(OUT/'android-apk-manifest.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:x for k,x in r.items() if k!='changed_asset_files'},indent=2))
