@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars32.bat" > "%~dp0eq-nil-build-env.log" 2>&1
if errorlevel 1 exit /b %errorlevel%
pushd "%~dp0"
cl /nologo /O2 /W4 /MT /Fe:native_eq_nil_harness.exe native_eq_nil_harness.c /link /BASE:0x30000000 /FIXED /DYNAMICBASE:NO /NXCOMPAT /SUBSYSTEM:CONSOLE bcrypt.lib > eq-nil-build.log 2>&1
set "eq_nil_build_result=%errorlevel%"
popd
exit /b %eq_nil_build_result%
