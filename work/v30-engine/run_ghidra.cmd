@echo off
setlocal
set "R=C:\Users\rwill\Documents\Opem Amalur"
set "E=%R%\work\v30-engine"
set "JAVA_HOME=%R%\tools\jdk-21.0.13+9"
set "PATH=%JAVA_HOME%\bin;%PATH%"
call "%R%\tools\ghidra_12.1.4_PUBLIC\support\launch.bat" fg jdk Ghidra-Headless 24G "" ghidra.app.util.headless.AnalyzeHeadless "%E%\ghidra" koa -import "%E%\koa.exe" -overwrite -scriptPath "%E%" -postScript CountFuncs.java "%E%" -analysisTimeoutPerFile 14400 > "%E%\ghidra.log" 2>&1
exit /b %ERRORLEVEL%
