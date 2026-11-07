@echo off
set "OA_BENCH_ROOT=C:\Users\rwill\Documents\Opem Amalur\work\v37-native-character"
set "OA_NDK=C:\Users\rwill\Documents\Opem Amalur\tools\android\android-ndk-r30"
set "OA_NINJA=C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\Ninja\ninja.exe"
"C:\Program Files\CMake\bin\cmake.exe" -S "%OA_BENCH_ROOT%\src\android\tools\replay" -B "%OA_BENCH_ROOT%\build-arm64" -G Ninja "-DCMAKE_MAKE_PROGRAM=%OA_NINJA%" "-DCMAKE_TOOLCHAIN_FILE=%OA_NDK%\build\cmake\android.toolchain.cmake" -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-29 -DANDROID_STL=c++_static -DCMAKE_BUILD_TYPE=Release -DCMAKE_POLICY_VERSION_MINIMUM=3.5 "-DFETCHCONTENT_SOURCE_DIR_LZ4=C:\Users\rwill\Documents\Opem Amalur\work\v32-native-benchmark\deps\lz4" "-DFETCHCONTENT_SOURCE_DIR_ZLIB=C:\Users\rwill\Documents\Opem Amalur\work\v32-native-benchmark\deps\zlib" "-DFETCHCONTENT_SOURCE_DIR_ZSTD=C:\Users\rwill\Documents\Opem Amalur\work\v32-native-benchmark\deps\zstd"
if errorlevel 1 exit /b %errorlevel%
"C:\Program Files\CMake\bin\cmake.exe" --build "%OA_BENCH_ROOT%\build-arm64" --target gfxrecon-replay -j 6
exit /b %errorlevel%
