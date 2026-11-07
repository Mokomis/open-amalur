@echo off
setlocal
cd /d "%~dp0"
set "ROOT=C:\Users\rwill\Documents\Opem Amalur"
call "%ROOT%\tools\android\android-ndk-r30\toolchains\llvm\prebuilt\windows-x86_64\bin\aarch64-linux-android26-clang.cmd" -std=c99 -Wall -Wextra -Werror -I. -I"%ROOT%\work\v19-host" -c oa_weighted_hardlight.c -o oa_weighted_hardlight-arm64.o > arm64-compile.log 2>&1
exit /b %errorlevel%
