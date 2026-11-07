@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars32.bat" > "%~dp0native-matrix-env.log" 2>&1
if errorlevel 1 exit /b %errorlevel%
cl /nologo /O2 /EHsc "%~dp0native_matrix_probe.cpp" /Fe:"%~dp0native-matrix-probe.exe" /Fo:"%~dp0native-matrix-probe.obj" /link /BASE:0x30000000 /DYNAMICBASE:NO > "%~dp0native-matrix-build.log" 2>&1
exit /b %errorlevel%
