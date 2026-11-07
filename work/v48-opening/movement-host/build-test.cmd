@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
"C:\Program Files\CMake\bin\cmake.exe" -S "C:\Users\rwill\Documents\Opem Amalur\work\v48-opening\movement-host" -B "C:\Users\rwill\Documents\Opem Amalur\work\v48-opening\movement-host\build" -G Ninja -DCMAKE_BUILD_TYPE=Debug -DCMAKE_MAKE_PROGRAM="C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja/ninja.exe"
if errorlevel 1 exit /b %errorlevel%
"C:\Program Files\CMake\bin\cmake.exe" --build "C:\Users\rwill\Documents\Opem Amalur\work\v48-opening\movement-host\build" --target oa-opening-movement-test
