@echo off
pushd "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cl /nologo /std:c11 /W4 /WX /O2 /D_CRT_SECURE_NO_WARNINGS oa_creation.c oa_creation_source_tables.c test_creation.c /Fe:test_creation.exe
set creation_build_result=%errorlevel%
if not "%creation_build_result%"=="0" (
 popd
 exit /b %creation_build_result%
)
test_creation.exe
set creation_test_result=%errorlevel%
popd
exit /b %creation_test_result%
