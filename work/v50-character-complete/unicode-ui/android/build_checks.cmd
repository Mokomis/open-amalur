@echo off
setlocal
cd /d "%~dp0"
set "ROOT=C:\Users\rwill\Documents\Opem Amalur"
set "JDK=%ROOT%\tools\jdk-21.0.13+9"
set "NDK=%ROOT%\tools\android\android-ndk-r30"
set "SDK=%ROOT%\tools\android\sdk"
set "PATH=%JDK%\bin;%PATH%"
if not exist classes mkdir classes
if not exist dex mkdir dex
"%JDK%\bin\javac.exe" -encoding UTF-8 -source 8 -target 8 -Xlint:all,-options -bootclasspath "%SDK%\android-35\android.jar" -d classes java\org\opemamalur\scene\TextRasterizer.java > javac.log 2>&1
if errorlevel 1 exit /b %errorlevel%
"%JDK%\bin\jar.exe" cf text-rasterizer.jar -C classes . > jar.log 2>&1
if errorlevel 1 exit /b %errorlevel%
call "%SDK%\android-15\d8.bat" --lib "%SDK%\android-35\android.jar" --min-api 26 --output dex text-rasterizer.jar > d8.log 2>&1
if errorlevel 1 exit /b %errorlevel%
call "%NDK%\toolchains\llvm\prebuilt\windows-x86_64\bin\aarch64-linux-android26-clang.cmd" -std=c99 -Wall -Wextra -Werror -O2 -fPIC -c oa_ui_text_android.c -o oa_ui_text_android.o > ndk-compile.log 2>&1
if errorlevel 1 exit /b %errorlevel%
call "%NDK%\toolchains\llvm\prebuilt\windows-x86_64\bin\aarch64-linux-android26-clang.cmd" -shared oa_ui_text_android.o -o liboa-ui-text-android-check.so -landroid -ljnigraphics -llog -lm > ndk-link.log 2>&1
if errorlevel 1 exit /b %errorlevel%
"%NDK%\toolchains\llvm\prebuilt\windows-x86_64\bin\llvm-readelf.exe" -h -d --dyn-syms liboa-ui-text-android-check.so > elf-validation.txt 2>&1
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > compiler-setup.log 2>&1
if errorlevel 1 exit /b %errorlevel%
cl /nologo /TC /std:c11 /O2 /W4 /WX test_utf16.c /Fe:test-utf16.exe > utf16-build.log 2>&1
if errorlevel 1 exit /b %errorlevel%
test-utf16.exe > utf16-results.txt 2>&1
exit /b %errorlevel%
