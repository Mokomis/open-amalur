@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > nul
cl /nologo /FI"C:\Users\rwill\Documents\Opem Amalur\work\v40-windows-host\include\desktop_compat.h" /std:c11 /W4 /c /I"C:\Users\rwill\Documents\Opem Amalur\work\v40-windows-host\include" /I"C:\Users\rwill\Documents\Opem Amalur\work\v40-windows-host\dependencies\include" "C:\Users\rwill\Documents\Opem Amalur\work\v44-native-fidelity\water-research\oa_native_water.c" /Fo:"C:\Users\rwill\Documents\Opem Amalur\work\v44-native-fidelity\water-research\oa_native_water.obj" > "C:\Users\rwill\Documents\Opem Amalur\work\v44-native-fidelity\water-research\compile-module.log" 2>&1
exit /b %errorlevel%
