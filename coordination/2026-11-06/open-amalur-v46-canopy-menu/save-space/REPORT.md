# Save Space compatibility

Changed only oa_menu.c/.h. Appended uint32_t space at offset88 in oa_save, increasing saves from88B to92B with unchanged OASAV002 magic. Missing Space is0/unknown; no location guess is made by this loader. Loader accepts exact88B or92B only, validates Space<=0x0fffffff and existing finite/world conditions, preserves caller state on failure. Writer rejects invalid Space before opening its output. Actual saves are written only through the existing user Save action.

An isolated actual-C harness passed248 checks under AddressSanitizer and UndefinedBehaviorSanitizer with -Wall -Wextra -Werror. It verifies both file sizes, five Space values, zero-default old files, exact88B prefix retention, old reader compatibility, missing/corrupt/truncated/trailing files, invalid numbers and invalid-writer preservation. Only private fixtures were written. Full engine/runtime testing belongs to the parent batch.

Root owns android_scene save.space assignment and stream restoration/unknown-identity fallback. This menu change supplies storage and does not itself infer or restore runtime Space. Backups: work/v46-canopy/before-save-space.
