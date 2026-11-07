@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cd /d "C:\Users\rwill\Documents\Opem Amalur\work\v50-character-complete\appearance-assets"
cl /nologo /std:c11 /D_CRT_SECURE_NO_WARNINGS /O2 /W4 oa_appearance.c test_appearance.c /Fe:test_appearance.exe
if errorlevel 1 exit /b %errorlevel%
test_appearance.exe model-test-inputs.txt
if errorlevel 1 exit /b %errorlevel%
cl /nologo /std:c11 /D_CRT_SECURE_NO_WARNINGS /O2 /W4 oa_appearance.c oa_appearance_selection.c test_selection.c /Fe:test_selection.exe
if errorlevel 1 exit /b %errorlevel%
test_selection.exe model-test-inputs.txt selected-default-plans.jsonl

if errorlevel 1 exit /b %errorlevel%
cl /nologo /std:c11 /D_CRT_SECURE_NO_WARNINGS /O2 /W4 oa_appearance.c oa_appearance_selection.c test_form_clips.c /Fe:test_form_clips.exe
if errorlevel 1 exit /b %errorlevel%
test_form_clips.exe model-test-inputs.txt clip-test-inputs.txt
