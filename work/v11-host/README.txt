Opem Amalur structural scene-container component

Scope
This component reads the candidate serialized-container layout observed in
five extracted .space_bxml variants. It does not yet decode a complete scene,
identify entity/component types, render geometry or invoke recovered scripts.
The parent investigation must corroborate the format with native loader evidence.

The admitted profile is:
  little-endian u32 payload byte count
  little-endian u32 fixup-table byte count
  payload bytes
  table of little-endian u32 payload-relative slot offsets
Each slot covers a four-byte relative target offset inside the payload.
Adjacent words are left uninterpreted. A target at payload end is admitted only
for zero-byte span access; offset zero is not assumed to mean a null pointer.

The loader owns an immutable copy of the original file and a sorted lookup
index. Original table ordering remains accessible. Serialized pointer fields
stay 32-bit offsets on both Windows x64 and Android arm64. No file field is
cast to or overwritten with a host address. The embedding importer owns file
SHA256, archive identity, symbol-label provenance and scene-schema selection.

Limits and errors
Default maximum input size is64MiB and maximum table slots1,048,576. The file
loader can temporarily hold both its read buffer and the immutable copy; these
are file-admission limits rather than a total-process memory quota. Overlong,
short, inconsistent, duplicate/overlapping and out-of-range structures fail.
Slot order need not be sorted, and no unconfirmed alignment is required.
Generic accessors report failure without inventing data. Float accessors only
interpret IEEE754 binary32 bits and do not imply finite scene coordinates.

Build on Windows
Use a Visual Studio developer shell and installed CMake:
  cmake -S work/v07-host -B work/v07-host/build-windows -G Ninja -DCMAKE_BUILD_TYPE=Release
  cmake --build work/v07-host/build-windows
  work/v07-host/build-windows/amalur-blob-test.exe
  work/v07-host/build-windows/amalur-blob-inspect.exe PATH_TO_SPACE --slots

Build for Android from Windows
  cmake -S work/v07-host -B work/v07-host/build-android -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_TOOLCHAIN_FILE=C:/path/to/ndk/build/cmake/android.toolchain.cmake -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-26
  cmake --build work/v07-host/build-android
The amalur_blob target propagates16KiB linker page options to its consumers.
Compilation and ELF inspection are separate from Android execution.

Integration
Include amalur_blob.h and link the CMake target amalur_blob. Keep the returned
blob alive while using const spans. Resolve byte spans through registered
slots, with a schema-verified element count and checked stride supplied by the
caller. The API intentionally has no dependency on Lua and no engine-service
implementations; scene-to-Lua/provider wiring is a later explicit layer.

Validation
The staged fixture executable checks section arithmetic, source immutability,
unsorted table order, exact float bits, registered-reference access, allocation
admission limits, missing files and malformed pointer spans. At staging time
these sources have not been built or executed by this worker. Parent execution
on Windows and Android artifact checks must be recorded before claiming them.
