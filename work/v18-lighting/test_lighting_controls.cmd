@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
cmake --build work\v18-host\build-windows --target amalur-exploration-input-test > outputs\scene-v18\comparison-test-build.log 2>&1
if errorlevel 1 exit /b %errorlevel%
work\v18-host\build-windows\amalur-exploration-input-test.exe > outputs\scene-v18\input-tests.txt
exit /b %errorlevel%
