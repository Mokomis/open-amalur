# Name input/rendering coverage: final read-only audit

Finding: the profile backend accepts and preserves1–16 valid UTF8 scalars, but the current interactive UI enters only an ASCII subset and renders only printable ASCII. Unicode naming is not end-to-end complete.

## Exact current evidence

- work/v19-host/oa_creation_ui.inc:23–26 appends ONE char byte; counts UTF8 leading bytes for the16-scalar budget. Lines35–37 physical key mapping accepts letters, digits, space and hyphen. It does not consume platform committed Unicode text, dead-key composition or IME text.
- Lines153–161 touch keyboard string isABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-'. The38keys add apostrophe; lowercase comes from the on-screen caps toggle. Space is separate at164. Physical apostrophe is not mapped. Other printable ASCII punctuation may validate/render but cannot be entered through these mapped controls.
- Lines28–31 Delete removes one UTF8 scalar boundary. Existing UTF8 bytes are copied on edit-open at87. Confirming an empty edit preserves the previous name at169–172.
- work/v19-host/oa_menu.c:58,75–80 supplies Android keycodes/actions to that mapping, not Unicode text.
- work/v19-host/oa_ui.h:26 declares exactly95glyphs per font. oa_ui.c:25–26 reads exactly95records. Lines60 and64 iterate bytes, replacing every byte outside32..126 with question-mark. Measurement and drawing both have this behavior.
- work/v20-char/build_ui.py:37 setsFIRST32,LAST126;46–63 bakes exactly those95codepoints for Cinzel/Alegreya. work/v21-ui/oa_ui.bin isOAUI0002 and follows that fixed schema. The installed font files may contain more glyphs, but this producer never puts them in the bank.

Consequently UTF8é(two bytes) would render??,中(three bytes) would render???, and a four-byte scalar would render????. The backend is not doing this conversion; it is a display limitation. An enlarged glyph atlas alone would still fail because byte iteration must also change.

## Backend/storage and defaults

work/v19-host/oa_creation.c:10–24 accepts strict non-overlong UTF8, rejects surrogates/out-of-range scalars and ASCIIcontrols/DEL, and limits16scalars/64bytes. This ASCII-control rejection is explicit custom host policy; the parent native audit of2031173.ui_bxml found no deny flags. Do not relabel all host validation choices as native restrictions.

set_name at176–178 copies the original UTF8 bytes. serialize230 and deserialize248 likewise retain bytes; validation runs on deserialize251. No Unicode-to-ASCII transliteration or normalization was found in these paths.

All8 source default names are printable ASCII and fit the font/input budgets: Elrid,Aidith,Stigandr,Isolda,Lorcan,Siobhan,Caerwyn,Niah (oa_creation_source_tables.c:6–13). Their stored bytes and rendering are unaffected. A pre-existing extended UTF8 name is preserved by load/edit-copy/unchanged-confirm but displays byte-wise question-marks; do not overwrite it merely to match the old glyph bank.

## Smallest honest remedy

To claim Unicode support, implement both:
1.Platform committed-text input/IME→complete valid UTF8 scalar sequences, atomically enforcing16scalars/64bytes. Retain scalar-boundary Delete. Windows surrogate pairs and Android IME composition need proper platform handling rather than more keycode constants.
2.UTF8 codepoint iteration shared by measuring/drawing plus codepoint→glyph mapping and suitable fallback fonts. Missing glyphs should produce one marker per scalar, not per UTF8 byte. The existing fixed95-record asset schema must be extended or have an independent dynamic text path.

An interim minimal honesty fix is to label the field as basic Latin entry, document its actual characters, and preserve already-stored UTF8 unchanged. This acknowledges the gap; it does not finish native-allowed name coverage. Do not impose a new ASCII-only backend restriction or infer a native deny-list.

No original game launch, live/source code, font bank or user-profile edits. This folder contains only the audit and source hashes. No claim is made that the original game's own font covers every Unicode scalar; the parent native contract establishes edit acceptance constraints, not universal font coverage.
