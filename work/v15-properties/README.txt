Open Amalur V15 native runtime Type reader

Run on the existing Windows project:
  python work\v15-properties\build_native_catalog.py
  python work\v15-properties\write_interaction_contract.py
  python work\v15-properties\verify_scene_scripts.py
  python work\v15-properties\recover_changed_scripts.py
  python work\v15-properties\run_decoder_validation.py

Dependencies already in project:
- work/v13-properties/compiled_type.py: guarded native Type carrier fields.
- work/v07-bxml/amalur_blob.py: native-confirmed carrier relocation inventory.
- src/amalur_script.py, src/amalur_reconstruct.py and existing native profile.
- Existing Lupa Lua5.1 for compilation of the two changed patch drafts.
- User-owned archives/extractions under work/scene-inputs-v09.

Correct runtime data is134225858_ksmt.batch, not compact batch_8130*.simtype_bxml.
Initial and patch variants stay separate. Native Workbench230417's408 bytes match
both variants exactly. The patch catalog has27350 records, matching the observed
native manager's27352 entries with two reserved indices. The reader structurally
checks all27350 entries, while retaining unknown component fields as opaque.

Original compact33-byte Workbench source is preserved, not decoded by this reader.
No runtime conversion of it is needed for the confirmed compiled-batch path.
Do not present structural parsing as full gameplay/component semantic recovery.

Runtime capture launch fix: earlier direct launches followed a short-lived process;
Steam then launched the real game under the logged-in desktop session. A native
capture succeeded after launching the REA/Frida worker in that desktop session,
with an already running Steam client, game CWD and per-process SteamAppId/GameId.
Original exe was not patched. All capture games closed and temporary tasks removed.
Capture workers are retained as one-time research tools with unique output scopes;
do not rerun them blindly or reuse old PIDs. They create outputs with exist_ok=False.

Gameplay integration remains separate: native source instance IDs are not native
generation handles. Workbench's original callback needs the alchemy UI/backend.
The on_interact native dispatch's two argument sources are documented without
inventing their handle roles. No Android interaction is enabled by this export.
