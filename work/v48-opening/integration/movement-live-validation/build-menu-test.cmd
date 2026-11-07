@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 exit /b %errorlevel%
"C:\Program Files\CMake\bin\cmake.exe" --build "C:\Users\rwill\Documents\Opem Amalur\work\v40-windows-host\build" --target oa-menu-test --parallel 8
exit /b %errorlevel%
