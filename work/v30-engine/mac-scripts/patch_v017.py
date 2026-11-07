"""Apply the live-confirmed sRGB table decoding and set version 0.17.0."""
from pathlib import Path
import re
host = Path.home() / "Documents/Opem Amalur/work/v19-host"
def edit(name, pairs):
    p = host / name
    t = p.read_text(encoding="utf-8")
    for old, new in pairs:
        if t.count(old) != 1:
            raise SystemExit("%s: expected one match for %r, found %d" % (name, old, t.count(old)))
        t = t.replace(old, new)
    p.write_text(t, encoding="utf-8", newline="")
source = (host / "room_lighting.c").read_text(encoding="utf-8")
m = re.search(r"glTexImage3D\(GL_TEXTURE_3D,0,GL_RGBA8,", source)
if not m:
    raise SystemExit("3D table upload not found: " + "; ".join(re.findall(r"glTexImage3D\([^;]*;", source)))
edit("room_lighting.c", [("glTexImage3D(GL_TEXTURE_3D,0,GL_RGBA8,", "glTexImage3D(GL_TEXTURE_3D,0,GL_SRGB8_ALPHA8,")])
edit("room_lighting_shader.h", [(" * Color LUT applied with the shader half-texel mapping; brightness and color_transition terms are not.\n", " * Color LUT applied with the shader half-texel mapping and sRGB decoding, as measured in the running game; brightness and color_transition terms are not.\n")])
edit("AndroidManifest.xml", [('android:versionCode="16" android:versionName="0.16.0"', 'android:versionCode="18" android:versionName="0.17.0"')])
edit("CMakeLists.txt", [("VERSION 0.16.0", "VERSION 0.17.0")])
edit("package_android.py", [("opem-amalur-scene-v0.16-arm64.apk", "opem-amalur-scene-v0.17-arm64.apk")])
print("patched")
