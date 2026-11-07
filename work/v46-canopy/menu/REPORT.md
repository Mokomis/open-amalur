# Persistent canopy menu option

Authoritative edits are ONLY work/v19-host/oa_menu.c and oa_menu.h. Backups preserve their exact pre-change bytes under work/v46-canopy/before-menu. No user settings or saves were opened or written by this work.

The Options menu has Canopy with Corrected/Dense values. settings.canopy_dense is appended to the existing settings struct; default0 is Corrected,1 is Dense. Existing dirty/autosave and Reset to Defaults paths handle it. Getter int oa_menu_canopy_dense(const oa_menu *m) returns normalized0/1, or0 forNULL. Renderer selection is intentionally external; root must apply the getter to its selector before exposing the built option. The menu itself makes no native-parity claim.

## Persistence

Magic OASET002 and the existing prefix remain unchanged. Loader accepts exact184B files (176B body, predating shadows),188B files (180B current body), and192B extended files (184B body). Missing fields are default-initialized: shadows1 when absent and canopy0. Existing HUD/look/invert/rate/shadows values survive. Save now emits192B. The old188B reader can read that file's unchanged prefix. Short, wrong-magic and trailing-byte files are rejected and retain defaults; invalid individual values still use existing sanitization. No migration write occurs merely by loading; normal menu dirty/autosave writes the extended format after a change.

## Input and layout

The existing value_row handles touch/mouse row taps, +/- buttons, controller left/right and keyboard arrows/accept. Canopy occupies focus index6 after Shadows. New row height56design units keeps10rows on the same page: Canopy y490..546 and Back676..732 of840design height, below title and above status754/footer796. Focus wraps all10widgets through the existing navigation logic. No pagination or extra state is required.

## Validation

An authorized isolated C harness in /private/tmp/oa-v46-menu-compat-qp0o9jeh compiled the actual current settings functions and pre-change backup functions, with their actual types/defaults/serializer. Assertions passed for184/188/192B load/write paths, exact176/180B preserved prefixes, both canopy roundtrips, the old reader consuming the new file, missing files, badmagic and invalid short/trailing sizes. sizeof/offsetof assertions confirm primitive32-bit layouts. It used only temporary fixtures. Actual-C-compatibility.json records the result and source hashes. No full-engine build was performed; parent owns Windows/Android builds and UI tests.

Root runtime checks should use an isolated test-data directory: open Options from title/pause; reach Canopy by keyboard/controller and touch; verify Dense getter1 and Corrected0 drive the finished selector; restart to verify persistence; confirm existing HUD/look/rate/shadows remain; Reset to Defaults should restore Corrected. Visual correctness of each canopy selector remains root's separate validation.

Final source SHA256:
oa_menu.c 91175598362d952ee8220992e52b41537da71fdca37e3974fb51a8e317083bbb
oa_menu.h 376bc49ece9f1e9617860ffe448eb69be2de2859950ce9ade508a926f245e5da

No lighting, foliage, stream, scene or waterfall implementation was changed by this menu task.
