@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > nul
cl /nologo /W4 /FI"..\..\..\v40-windows-host\include\desktop_compat.h" /I"..\..\..\v40-windows-host\include" /I"..\..\..\v40-windows-host\dependencies\include" /I"..\..\..\v19-host" scene_profile_test.c "..\..\..\v19-host\oa_scene_profile.c" /Fe:scene-profile-test.exe
if errorlevel 1 exit /b %errorlevel%
scene-profile-test.exe
