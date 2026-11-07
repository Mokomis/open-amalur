@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
if errorlevel 1 goto finished
set "PATH=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja;%PATH%"
"C:\Program Files\CMake\bin\cmake.exe" -S "C:\Users\rwill\Documents\Opem Amalur\work\v33-native-camera\src" -B "C:\Users\rwill\Documents\Opem Amalur\work\v45-foliage-coverage\replay-dump-capability\build" -G Ninja -DCMAKE_BUILD_TYPE=Release -DD3D12_SUPPORT=OFF -DGFXRECON_ENABLE_OPENXR=OFF -DGFXRECON_TOCPP_SUPPORT=OFF -DBUILD_STATIC=ON -DBUILD_WERROR=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5 -DFETCHCONTENT_SOURCE_DIR_LZ4="C:\Users\rwill\Documents\Opem Amalur\work\v32-native-benchmark\deps\lz4" -DFETCHCONTENT_SOURCE_DIR_ZSTD="C:\Users\rwill\Documents\Opem Amalur\work\v32-native-benchmark\deps\zstd" -DFETCHCONTENT_SOURCE_DIR_ZLIB="C:\Users\rwill\Documents\Opem Amalur\work\v32-native-benchmark\deps\zlib"
if errorlevel 1 goto finished
"C:\Program Files\CMake\bin\cmake.exe" --build "C:\Users\rwill\Documents\Opem Amalur\work\v45-foliage-coverage\replay-dump-capability\build" --target gfxrecon-replay -j 3
:finished
set "OA_DUMP_BUILD_EXIT=%errorlevel%"
echo %OA_DUMP_BUILD_EXIT% > "C:\Users\rwill\Documents\Opem Amalur\work\v45-foliage-coverage\replay-dump-capability\build-exit-code.txt"
exit /b %OA_DUMP_BUILD_EXIT%
