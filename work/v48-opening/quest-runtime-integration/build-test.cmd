@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cd /d "C:\Users\rwill\Documents\Opem Amalur\work\v48-opening\quest-runtime-integration"
cl /nologo /std:c11 /W4 /WX /O2 /D_CRT_SECURE_NO_WARNINGS oa_mq01_cursor.c test_mq01_cursor.c /Fe:test_mq01_cursor.exe
if errorlevel 1 exit /b %errorlevel%
test_mq01_cursor.exe >test-results.json
if errorlevel 1 exit /b %errorlevel%
"C:\Users\rwill\Documents\Opem Amalur\tools\android\android-ndk-r30\toolchains\llvm\prebuilt\windows-x86_64\bin\clang.exe" --target=aarch64-linux-android26 --sysroot="C:\Users\rwill\Documents\Opem Amalur\tools\android\android-ndk-r30\toolchains\llvm\prebuilt\windows-x86_64\sysroot" -std=c99 -Wall -Wextra -Werror -O2 oa_mq01_cursor.c test_mq01_cursor.c -o test_mq01_cursor_arm64
if errorlevel 1 exit /b %errorlevel%
