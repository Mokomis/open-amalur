@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > nul
cl /nologo /W4 /I"include" /I"..\..\v19-host" render_cache_test.c "..\..\v19-host\oa_render_cache.c" "..\..\v19-host\oa_cpu_policy.c" /Fe:render-cache-test.exe
if errorlevel 1 exit /b %errorlevel%
render-cache-test.exe
