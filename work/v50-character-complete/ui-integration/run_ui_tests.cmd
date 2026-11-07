@echo off
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cl /nologo /std:c11 /W3 /D_CRT_SECURE_NO_WARNINGS /I"..\..\v19-host" /I"..\..\v19-host\tests\input_stubs" test_creator_ui.c ..\..\v19-host\oa_menu.c ..\..\v19-host\oa_items.c ..\..\v19-host\exploration_input.c ..\..\v19-host\oa_creation.c ..\..\v19-host\oa_creation_source_tables.c ..\..\v19-host\oa_creation_draft.c /Fe:test_creator_ui.exe
if errorlevel 1 exit /b %errorlevel%
test_creator_ui.exe test-user-data
