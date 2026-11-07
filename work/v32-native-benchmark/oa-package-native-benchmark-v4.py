import hashlib,json,subprocess,zipfile,shutil
from pathlib import Path
r=Path(r'C:\Users\rwill\Documents\Opem Amalur\work\v32-native-benchmark')
tools=Path(r'C:\Users\rwill\Documents\Opem Amalur\tools')
buildtools=tools/'android/sdk/android-15';sdkjar=tools/'android/sdk/android-35/android.jar';jdk=tools/'jdk-21.0.13+9/bin'
apk=r/'apk-static-resources';apk.mkdir(exist_ok=True)
manifest='''<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.openamalur.nativebenchmark" android:versionCode="4" android:versionName="0.4-static-resources"><uses-sdk android:minSdkVersion="29" android:targetSdkVersion="35"/><uses-feature android:name="android.hardware.vulkan.level" android:version="1" android:required="true"/><application android:label="Open Amalur Native Benchmark" android:hasCode="false" android:debuggable="true" android:extractNativeLibs="true" android:theme="@android:style/Theme.Material.NoActionBar.Fullscreen"><activity android:name="android.app.NativeActivity" android:exported="true" android:screenOrientation="landscape" android:configChanges="orientation|screenSize|keyboard|keyboardHidden|screenLayout"><meta-data android:name="android.app.lib_name" android:value="gfxrecon-replay"/><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter></activity></application></manifest>'''
(apk/'AndroidManifest.xml').write_text(manifest)
def run(a):subprocess.run([str(x) for x in a],check=True)
run([buildtools/'aapt2.exe','link','--manifest',apk/'AndroidManifest.xml','-I',sdkjar,'-o',apk/'base-unsigned.apk'])
shutil.copyfile(r/'build-arm64/libgfxrecon-replay.so',apk/'libgfxrecon-replay.so')
run([tools/'android/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-strip.exe','--strip-unneeded',apk/'libgfxrecon-replay.so'])
with zipfile.ZipFile(apk/'base-unsigned.apk','a',compression=zipfile.ZIP_DEFLATED) as z:z.write(apk/'libgfxrecon-replay.so','lib/arm64-v8a/libgfxrecon-replay.so')
run([buildtools/'zipalign.exe','-f','-p','4',apk/'base-unsigned.apk',apk/'aligned.apk'])
key=r/'native-benchmark-debug.keystore'
if not key.exists():run([jdk/'keytool.exe','-genkeypair','-noprompt','-keystore',key,'-storepass','android','-keypass','android','-alias','benchmark','-keyalg','RSA','-keysize','2048','-validity','3650','-dname','CN=OpenAmalurNativeBenchmark'])
run([jdk/'java.exe','-jar',buildtools/'lib/apksigner.jar','sign','--ks',key,'--ks-key-alias','benchmark','--ks-pass','pass:android','--key-pass','pass:android','--out',apk/'open-amalur-native-benchmark.apk',apk/'aligned.apk'])
run([jdk/'java.exe','-jar',buildtools/'lib/apksigner.jar','verify','--verbose',apk/'open-amalur-native-benchmark.apk'])
info={'package':'org.openamalur.nativebenchmark','upstream_commit':'9a673d202dc42a7cebadd9854c940f4209819279','apk_sha256':hashlib.sha256((apk/'open-amalur-native-benchmark.apk').read_bytes()).hexdigest(),'library_sha256':hashlib.sha256((apk/'libgfxrecon-replay.so').read_bytes()).hexdigest(),'purpose':'Captured scene replay and repeating graphics benchmark; no gameplay','original_signing_key_used':False}
(apk/'build-info.json').write_text(json.dumps(info,indent=2)+'\n');print(json.dumps(info,indent=2))
