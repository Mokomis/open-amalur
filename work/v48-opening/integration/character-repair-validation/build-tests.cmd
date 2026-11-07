@echo off
setlocal
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
cl /nologo /std:c11 /O2 /W4 /WX /D_CRT_SECURE_NO_WARNINGS /I"C:\Users\rwill\Documents\Opem Amalur\work\v19-host" test_character_repairs.c "C:\Users\rwill\Documents\Opem Amalur\work\v19-host\oa_character_attributes.c" /Fe:test_character_repairs.exe
exit /b %errorlevel%
