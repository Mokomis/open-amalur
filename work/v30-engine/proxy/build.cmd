@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul
cd /d "%~dp0"
cl /nologo /O2 /W3 /MT /LD /D_CRT_SECURE_NO_WARNINGS oa_d3d11.c oa_engine.c /Fe:d3d11.dll /link /DEF:oa_d3d11.def kernel32.lib
exit /b %ERRORLEVEL%
