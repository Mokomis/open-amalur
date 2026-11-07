@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul
if errorlevel 1 exit /b %errorlevel%
cd /d "C:\Users\rwill\Documents\Opem Amalur\work\v43-scene-fidelity\placement-research"
cl /nologo /O2 /EHsc /D_CRT_SECURE_NO_WARNINGS barrel_native_pose.cpp /Fe:barrel_native_pose.exe /link /BASE:0x30000000 /DYNAMICBASE:NO
exit /b %errorlevel%
