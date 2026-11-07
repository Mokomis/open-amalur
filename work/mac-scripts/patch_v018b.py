from pathlib import Path
host = Path.home() / "Documents/Opem Amalur/work/v19-host"
p = host / "build_validate.cmd"; b = p.read_bytes().decode()
a = "--target amalur-exploration-input-test --parallel 8"
assert b.count(a) == 1; b = b.replace(a, "--target amalur-exploration-input-test oa-character-test --parallel 8")
nl = "\r\n" if "\r\n" in b else "\n"
a = "work\\v19-host\\build-windows\\amalur-exploration-input-test.exe > outputs\\scene-v19\\input-tests.txt 2>&1" + nl + "if errorlevel 1 exit /b %errorlevel%" + nl
assert b.count(a) == 1; b = b.replace(a, a + "work\\v19-host\\build-windows\\oa-character-test.exe work\\v20-char\\character.bin > outputs\\scene-v19\\character-tests.txt 2>&1" + nl + "if errorlevel 1 exit /b %errorlevel%" + nl)
p.write_bytes(b.encode())
p = host / "package_android.py"; b = p.read_bytes().decode()
assert b.count("opem-amalur-scene-v0.17-arm64.apk") == 1; b = b.replace("opem-amalur-scene-v0.17-arm64.apk", "opem-amalur-scene-v0.18-arm64.apk")
a = "files['assets/collision.bin']=root/'outputs/scene-v17/collision.bin'"
assert b.count(a) == 1; b = b.replace(a, a + "\nfiles['assets/character.bin']=root/'work/v20-char/character.bin'")
p.write_bytes(b.encode())
print("patched rest")
