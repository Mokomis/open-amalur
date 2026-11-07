@echo off
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cl /nologo /std:c11 /W3 /D_CRT_SECURE_NO_WARNINGS /I"..\..\v19-host" test_presets.c ..\..\v19-host\oa_creation.c ..\..\v19-host\oa_creation_source_tables.c /Fe:test_presets.exe
if errorlevel 1 exit /b %errorlevel%
test_presets.exe
