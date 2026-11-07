@echo off
setlocal
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > compiler-setup.log 2>&1
if errorlevel 1 exit /b %errorlevel%
cl /nologo /TC /std:c11 /W4 /WX /utf-8 /D_CRT_SECURE_NO_WARNINGS oa_desktop_name_input.c test_name_input_win32.c /Fe:test-name-input-win32.exe /link user32.lib gdi32.lib > build.log 2>&1
exit /b %errorlevel%
