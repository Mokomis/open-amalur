@echo off
setlocal
set "GHIDRA_INSTALL_DIR=%~dp0tools\ghidra_12.1.4_PUBLIC"
set "JAVA_HOME=%~dp0tools\jdk-21.0.13+9"
set "REA_ANALYSIS_PROVIDER=ghidra"
set "REA_GHIDRA_STARTUP_TIMEOUT_MS=900000"
node "%~dp0tools\rea\node_modules\rea-agents\scripts\rea.mjs" %*
exit /b %errorlevel%
