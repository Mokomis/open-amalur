@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul
if errorlevel 1 exit /b %errorlevel%
cd /d "C:\Users\rwill\Documents\Opem Amalur\work\v33-native-camera"
cl /nologo /O2 /fp:strict /EHsc /D_CRT_SECURE_NO_WARNINGS oa-matrix-original-proof.cpp /Fe:oa-matrix-original-proof.exe
if errorlevel 1 exit /b %errorlevel%
oa-matrix-original-proof.exe abc070-original-code.bin matrix-proof-inputs.bin matrix-proof-original-output.bin
if errorlevel 1 exit /b %errorlevel%
"C:\Users\rwill\Documents\Opem Amalur\tools\android\android-ndk-r30\toolchains\llvm\prebuilt\windows-x86_64\bin\aarch64-linux-android29-clang++.cmd" -std=c++17 -O2 -ffp-contract=off -static-libstdc++ -Wall -Wextra -Werror oa-matrix-arm-proof.cpp -o oa-matrix-arm-proof
exit /b %errorlevel%
