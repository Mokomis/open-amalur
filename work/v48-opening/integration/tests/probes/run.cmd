@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > nul
cl /nologo /W4 /I"include" /I"..\..\..\..\v19-host" probe_registry_test.c "..\..\..\..\v19-host\oa_material_probes.c" /Fe:probe-registry-test.exe
if errorlevel 1 exit /b %errorlevel%
probe-registry-test.exe
