@echo off
setlocal
cd /d "%~dp0"
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat" > compiler-setup.log 2>&1
if errorlevel 1 exit /b %errorlevel%
lib /nologo /def:libEGL-fixture.def /machine:x64 /out:libEGL-fixture.lib > imports.log 2>&1
if errorlevel 1 exit /b %errorlevel%
lib /nologo /def:libGLESv2-fixture.def /machine:x64 /out:libGLESv2-fixture.lib >> imports.log 2>&1
if errorlevel 1 exit /b %errorlevel%
cl /nologo /TC /std:c11 /MDd /O2 /Gy /Gw /W3 /D_CRT_SECURE_NO_WARNINGS /DOA_DESKTOP=1 /FI"C:\Users\rwill\Documents\Opem Amalur\work\v40-windows-host\include\desktop_compat.h" /Iinputs /I"C:\Users\rwill\Documents\Opem Amalur\work\v40-windows-host\include" /I"C:\Users\rwill\Documents\Opem Amalur\work\v40-windows-host\dependencies\include" /I"C:\Users\rwill\Documents\Opem Amalur\work\v08-portable\include" /I"C:\Users\rwill\Documents\Opem Amalur\work\v08-portable\third_party\lua-5.1.5\src" test_creation_session_gpu.c inputs/oa_appearance.c inputs/oa_appearance_selection.c inputs/oa_canopy.c inputs/oa_cart_probe.c inputs/oa_character_appearance.c inputs/oa_cosmetic_material.c inputs/oa_cosmetic_texture_bank.c inputs/oa_cpu_policy.c inputs/oa_creation.c inputs/oa_creation_gameplay.c inputs/oa_creation_session.c inputs/oa_creation_source_tables.c inputs/oa_creator_game.c inputs/oa_material_probes.c inputs/oa_mq01_cursor.c inputs/oa_native_ao.c inputs/oa_native_bloom.c inputs/oa_native_dof.c inputs/oa_native_filter.c inputs/oa_post.c inputs/oa_render_cache.c inputs/oa_stream.c inputs/opem_collision.c /Fe:test-creation-session-gpu.exe /link /OPT:REF /OPT:ICF libEGL-fixture.lib libGLESv2-fixture.lib inputs/oa_opening_runtime.lib inputs/amalur_runtime.lib inputs/amalur_lua51.lib > build.log 2>&1
exit /b %errorlevel%
