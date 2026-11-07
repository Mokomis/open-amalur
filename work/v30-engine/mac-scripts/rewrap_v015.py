"""Rewrap the v0.15.0 APK as v0.15.1 so it can replace v0.16.0 without losing app data.

Android refuses a lower versionCode on a non-debuggable package. Every payload entry is
copied unchanged from the v0.15.0 APK; only the manifest version and the signature differ.
"""
from pathlib import Path
import difflib, hashlib, json, re, subprocess, zipfile

root = Path.home() / "Documents" / "Opem Amalur"
stage = root / "work/v19-rollback"
out = root / "outputs/scene-v19"
source = out / "opem-amalur-scene-v0.15-arm64.apk"
apk = out / "opem-amalur-scene-v0.15.1-arm64.apk"
sdk = root / "tools/android/sdk"
bt = sdk / "android-15"
java = root / "tools/jdk-21.0.13+9/bin/java.exe"
key = root / "tools/android/opem-scene-debug.keystore"
SOURCE_SHA = "21e04375d5869ed181a4c947d92a1dd4766b991f746b3612fcdc38e4443700de"
REPLACED = {"AndroidManifest.xml", "resources.arsc"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(args):
    result = subprocess.run([str(a) for a in args], capture_output=True, timeout=180)
    if result.returncode:
        # Output only; the argument list can hold the store password.
        raise RuntimeError("%s exit %d: %s" % (Path(str(args[0])).name, result.returncode, result.stderr.decode(errors="replace")[:800]))
    return result.stdout.decode("utf-8", errors="replace")


def xmltree(path):
    return run([bt / "aapt2.exe", "dump", "xmltree", path, "--file", "AndroidManifest.xml"]).splitlines()


if sha(source.read_bytes()) != SOURCE_SHA:
    raise RuntimeError("v0.15.0 APK hash changed")
if apk.exists():
    raise RuntimeError("Refusing to overwrite " + apk.name)

manifest = stage / "AndroidManifest.xml"
text = (root / "work/v19-host/AndroidManifest.xml").read_text(encoding="utf-8")
text = text.replace('android:versionCode="16"', 'android:versionCode="17"').replace('android:versionName="0.16.0"', 'android:versionName="0.15.1"')
if 'versionCode="17"' not in text or 'versionName="0.15.1"' not in text:
    raise RuntimeError("Manifest version not replaced")
manifest.write_text(text, encoding="utf-8")

unsigned, aligned = stage / "unsigned.apk", stage / "aligned.apk"
run([bt / "aapt2.exe", "link", "-o", unsigned, "--manifest", manifest, "-I", sdk / "android-35/android.jar", "--min-sdk-version", "26", "--target-sdk-version", "35"])
with zipfile.ZipFile(source) as old, zipfile.ZipFile(unsigned, "a") as new:
    for entry in old.infolist():
        if entry.filename not in REPLACED:
            new.writestr(entry.filename, old.read(entry.filename), compress_type=entry.compress_type)
run([bt / "zipalign.exe", "-f", "4", unsigned, aligned])

packager = (root / "work/v19-host/package_android.py").read_text(encoding="utf-8")
store = re.search(r"'--ks-pass','pass:([^']*)'", packager).group(1)
keypass = re.search(r"'--key-pass','pass:([^']*)'", packager).group(1)
run([java, "-jar", bt / "lib/apksigner.jar", "sign", "--ks", key, "--ks-key-alias", "opem-scene-debug", "--ks-pass", "pass:" + store, "--key-pass", "pass:" + keypass, "--v1-signing-enabled", "false", "--v2-signing-enabled", "true", "--v3-signing-enabled", "true", "--out", apk, aligned])
verify = run([java, "-jar", bt / "lib/apksigner.jar", "verify", "--verbose", "--print-certs", apk])
run([bt / "zipalign.exe", "-c", "4", apk])

with zipfile.ZipFile(source) as old, zipfile.ZipFile(apk) as new:
    old_names = {n for n in old.namelist() if n not in REPLACED}
    new_names = {n for n in new.namelist() if n not in REPLACED}
    if old_names != new_names:
        raise RuntimeError("Entry sets differ: %s" % sorted(old_names ^ new_names))
    for name in old_names:
        if sha(old.read(name)) != sha(new.read(name)):
            raise RuntimeError("Payload differs: " + name)
    arsc_same = sha(old.read("resources.arsc")) == sha(new.read("resources.arsc"))
    library = sha(new.read("lib/arm64-v8a/libopem_amalur_scene.so"))

changes = [l for l in difflib.ndiff(xmltree(source), xmltree(apk)) if l[:2] in ("- ", "+ ")]
digest = lambda text: re.search(r"SHA-256 digest: (\w+)", text).group(1)
old_cert = digest(run([java, "-jar", bt / "lib/apksigner.jar", "verify", "--print-certs", source]))
receipt = {
    "apk": apk.name, "sha256": sha(apk.read_bytes()), "bytes": apk.stat().st_size,
    "source_apk": source.name, "source_sha256": SOURCE_SHA,
    "payload_entries_identical": len(old_names), "resources_arsc_identical": arsc_same,
    "library_sha256": library, "manifest_changes": changes,
    "signer_matches_source": digest(verify) == old_cert,
    "reason": "Android refuses a lower versionCode on a non-debuggable package; uninstalling would erase app data",
}
(out / "rollback-v0.15.1.json").write_text(json.dumps(receipt, indent=2))
print(json.dumps(receipt, indent=2))
