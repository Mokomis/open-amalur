@echo off
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul
cl /nologo /std:c11 /experimental:c11atomics /W3 /D_CRT_SECURE_NO_WARNINGS /DOA_DESKTOP=1 /FI"C:\Users\rwill\Documents\Opem Amalur\work\v40-windows-host\include\desktop_compat.h" /I. /I"C:\Users\rwill\Documents\Opem Amalur\work\v40-windows-host\include" /I"C:\Users\rwill\Documents\Opem Amalur\work\v40-windows-host\dependencies\include" /I"C:\Users\rwill\Documents\Opem Amalur\work\v19-host" /c /Tcdesktop_platform.c.staged /Fodesktop_platform-stage.obj > host-compile.log 2>&1
exit /b %errorlevel%
