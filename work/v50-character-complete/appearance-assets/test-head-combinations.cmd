@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cd /d "C:\Users\rwill\Documents\Opem Amalur\work\v50-character-complete\appearance-assets"
cl /nologo /std:c11 /D_CRT_SECURE_NO_WARNINGS /O2 /W4 oa_appearance.c oa_appearance_selection.c test_selection.c /Fe:test_selection.exe
if errorlevel 1 exit /b %errorlevel%
test_selection.exe model-test-inputs.txt selected-default-plans.jsonl
