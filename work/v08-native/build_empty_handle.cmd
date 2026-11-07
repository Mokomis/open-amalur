@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars32.bat" > "%~dp0empty-handle-build-env.log" 2>&1
if errorlevel 1 exit /b %errorlevel%
pushd "%~dp0"
cl /nologo /O2 /W4 /MT /Fe:native_empty_handle_harness.exe native_empty_handle_harness.c /link /BASE:0x30000000 /FIXED /DYNAMICBASE:NO /NXCOMPAT /SUBSYSTEM:CONSOLE bcrypt.lib > empty-handle-build.log 2>&1
set "empty_handle_build_result=%errorlevel%"
popd
exit /b %empty_handle_build_result%
