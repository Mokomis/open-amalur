$note=@'

V0.18.0 CHARACTER (2026-10-31): tablet 99cc517a runs a visible animated third-person character, versionCode 19. APK outputs/scene-v19/opem-amalur-scene-v0.18-arm64.apk sha256 starts ef8edee1b91e8049. The tablet was on Wi-Fi ADB at 192.168.68.55:45765 at install (same serial), USB serial 99cc517a was absent.
FORMATS: Sony Edge Animation port. Clips tag EA05 (blob = file+8; u32 ms, u32 size, blob, 1 byte). Skeletons tag ES03 at file+4. From struct start: joints u16 +0x10, bind pose rel +0x18 (r,t,s 48 bytes), parents rel +0x1c, names rel +0x20. Native quaternions must be conjugated to compose as parent*local (verified: head z175, stored inverse bind t error 0 on most parts). Decompressor 0x111bf10(out,user,anim,setData,count,frame,alpha); blend tree 0x111d1a0, caller 0xce58c0; set tables anim+0x3c (u16 base,count) and +0x38 (u16 size at +2, u32 offset at +4). Loader RigAnimation 0xd14240.
VERTICES stride 60: pos 3f, joints 4u8, weights 4u16/32767, uv 2f at +24, normal 3i16 at +32, tangent, binormal, color. Vertex joint indexes a per-FAB palette of 52-byte records after names: inverse bind t 3f + pad, q 4f, s 3f, count, FAB joint index. Stored inverse q is the conjugate of the composing convention.
TOOLS: work/v20-char/clip_bake.cpp runs only the pure decompressor in a private image copy; build_character.py makes work/v20-char/character.bin; symbols.json holds names. Clips idle 457525, walk 457557, run 457536. hero_* clips are stubs. Parts: me_armor torso 1926576, legs 1926575, hands 1926574, feet 1923507, majestic_head 301406 as an explicit preview choice, not native player assembly.
RUNTIME: work/v19-host/oa_character.c, oa_character_gl.c; 980 character checks plus 45 input checks passed. Movement speed 420, boom 240 and clip thresholds are authored. Motion tree 100644 is not used.
KNOWN ISSUES: camera boom only avoids collision geometry, so it can pass through props such as shelves; maroon rug is an untextured fallback; no weapon, face detail or hair; foot sliding not measured. NEXT: combat in the shop before exterior work, because terrain_bin is undecoded.
'@
Add-Content -Encoding UTF8 'work\CURRENT_STATE.txt' $note
Add-Content -Encoding UTF8 'outputs\scene-v19\PROGRESS.txt' $note
'noted'
python -I 'work\v19-capture\state_manifest.py' compare 'work\v19-capture\state-before' 2>&1 | ForEach-Object { "$_" }
(Get-Process java -ErrorAction SilentlyContinue | Measure-Object).Count
