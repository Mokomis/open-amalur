@echo off
setlocal
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >compiler.log 2>&1
if errorlevel 1 exit /b %errorlevel%
cl /nologo /TC /std:c11 /W4 /WX /c oa_patron_presentation.c /Fo:oa_patron_presentation-win.obj >compile-win.log 2>&1
if errorlevel 1 exit /b %errorlevel%
call "C:\Users\rwill\Documents\Opem Amalur\tools\android\android-ndk-r30\toolchains\llvm\prebuilt\windows-x86_64\bin\aarch64-linux-android26-clang.cmd" -std=c99 -Wall -Wextra -Werror -c oa_patron_presentation.c -o oa_patron_presentation-arm64.o >compile-arm64.log 2>&1
exit /b %errorlevel%
