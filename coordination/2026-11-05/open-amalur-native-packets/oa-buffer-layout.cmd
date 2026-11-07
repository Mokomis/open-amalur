@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul
if errorlevel 1 exit /b %errorlevel%
cd /d "C:\Users\rwill\Documents\Opem Amalur\work\v34-native-packets"
cl /nologo /O2 /W3 oa-buffer-layout.c /Fe:oa-buffer-layout.exe
if errorlevel 1 exit /b %errorlevel%
oa-buffer-layout.exe
