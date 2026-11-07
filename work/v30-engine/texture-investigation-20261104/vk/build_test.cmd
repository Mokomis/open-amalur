@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul
cd /d "%~dp0"
cl /nologo /O2 /W3 /MT /D_CRT_SECURE_NO_WARNINGS dxbc_test.c oa_dxbc.c /Fe:dxbc_test.exe
exit /b %ERRORLEVEL%
