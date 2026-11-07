def sub(path,pairs):
    s=open(path,encoding='utf-8',newline='').read()
    for a,b in pairs:
        assert s.count(a)==1,a
        s=s.replace(a,b)
    open(path,'w',encoding='utf-8',newline='').write(s)
sub('README.md',[
("| `work/v15-properties/`, `outputs/scene-v15/` | Confirmed compiled native type decoder and real Workbench record evidence |","| `work/v15-properties/`, `outputs/scene-v15/` | Confirmed compiled native type decoder; Workbench record evidence is in the release, with progress notes in Git |"),
("| `work/v18-lighting/`, `outputs/scene-v18/` | Lighting extraction, native evidence and package validation |","| `work/v18-lighting/`, `outputs/scene-v18/` | Lighting extraction code; native evidence and package validation are in the release, with progress notes in Git |"),
("| `references/` | Reference research/source with original notices; revisions recorded in backup metadata |","| `references/` | Reference research/source with original notices; `references/manifest.json` records upstream revisions |"),
("| `mac-coordination/` | Additional Mac-side files whose content differs from or is absent on Windows |\n","| `outputs/` | Reports, `PROGRESS.txt`/`continuation.json` notes, and the test inputs `native-script-profile.json` and `reconstruction-v03/`; everything else is in the release |\n"),
("Git contains browsable source and selected research. The private checkpoint release contains the larger project, evidence, recovered-script corpus, and build artifacts.","Git contains source, build recipes, tests and notes. The private checkpoint release contains the larger project, evidence, recovered-script corpus, generated outputs and build artifacts; a clone alone cannot build the APK or run the 18 tests that need original script fixtures."),
("Third-party code keeps its original licenses and attribution.","Third-party code keeps its original licenses and attribution. Reference projects with no license file (DevCortez/KoaModFramework, ZucchiniZap/AmalurBxmlConverter, mburbea/ModelSwapper) are not in Git; they are in the release, with revisions in `references/manifest.json`."),
])
sub('BACKUP_AND_RESTORE.md',[
("The Git source view is intentionally smaller than the complete private checkpoint. A file missing from Git may still be fully preserved in a release archive; consult the manifests.",
"""The Git source view is intentionally smaller than the complete private checkpoint. A file missing from Git may still be fully preserved in a release archive; consult the manifests.

Git history was rewritten on 2026-10-31 to remove generated data. Each removed file was hash-checked inside the release archive listed here before the rewrite:

| Removed from Git | Release archive |
| --- | --- |
| `outputs/`, except notes and test inputs | `open-amalur-windows-evidence-2026-10-31.zip` |
| `src/scene-v*/`, `.log` and `.png` files under `work/`, and the three unlicensed reference folders | `open-amalur-windows-project-2026-10-31.zip` |
| `mac-coordination/` (paths in the archive omit this prefix) | `open-amalur-mac-additions-2026-10-31.zip` |

The manifests are unchanged, so their `git` fields describe the original checkpoint rather than current Git contents. `backup-metadata/SHA256SUMS` pins the release's copy of this document, so this edited copy will not match that entry; `verify_backup.py` checks the release copy."""),
])
