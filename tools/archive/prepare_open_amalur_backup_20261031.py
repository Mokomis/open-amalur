"""Read-only project snapshot. Run on Windows; writes only to a separate backup folder."""
from pathlib import Path
import collections
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import time
import zipfile

ROOT = Path(r"C:\Users\rwill\Documents\Opem Amalur")
DEST = Path(r"C:\Users\rwill\Documents\Open Amalur Backups\2026-10-31")
GIT = DEST / "git"
DEST.mkdir(parents=True, exist_ok=True)
GIT.mkdir(exist_ok=True)
DATE = "2026-10-31"
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".pytest_cache", ".gradle"}
SECRET_SUFFIXES = {".keystore", ".jks", ".pem", ".p12", ".pfx", ".key"}
TEXT_SUFFIXES = {".py", ".c", ".cpp", ".h", ".hpp", ".lua", ".js", ".ts", ".json", ".jsonl", ".txt", ".md", ".log", ".cmd", ".bat", ".ps1", ".sh", ".cmake", ".xml", ".patch", ".diff", ".ini", ".toml", ".yml", ".yaml", ".csv", ".inc", ".properties", ".html", ".glsl", ".vert", ".frag"}
CORPUS_DIRS = {"corpus-drafts-v03", "initial-corpus-drafts-v04", "initial-corpus-drafts-v05"}
ARCHIVES = {
    "project": f"open-amalur-windows-project-{DATE}.zip",
    "evidence": f"open-amalur-windows-evidence-{DATE}.zip",
    "corpus": f"open-amalur-recovered-script-corpus-{DATE}.zip",
}


def sha_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def exclusion(rel):
    parts = rel.parts
    if any(p in SKIP_DIRS for p in parts):
        return "reinstallable dependency, version-control metadata or cache"
    if any(p.startswith("native-state-before") for p in parts):
        return "private native-game save/configuration backup; preserved locally"
    if rel.suffix.lower() in SECRET_SUFFIXES or rel.name.lower() in {".env", ".npmrc", ".pypirc", "id_rsa", "id_ed25519", "credentials.json"}:
        return "private signing key or credential configuration; preserved locally"
    if parts[0] == "tools" and (len(parts) < 3 or parts[1] not in {"rea", "rea-frida", "lua-validation"}):
        return "downloaded toolchain; reinstall using recorded dependency versions"
    return None


def scope(rel):
    if rel.parts[0] == "outputs":
        if (len(rel.parts) > 1 and rel.parts[1] in CORPUS_DIRS) or rel.name.startswith("opem-amalur-initial-script-drafts-"):
            return "corpus"
        return "evidence"
    return "project"


def git_include(rel, size):
    if size > 2_000_000:
        return False
    if any(p.startswith("build-") or p in {"build", "CMakeFiles", "audit"} for p in rel.parts):
        return False
    if rel.parts[0] == "references":
        return True if rel.suffix.lower() in TEXT_SUFFIXES or rel.name.lower().startswith(("license", "copying", "notice", "readme")) else False
    if rel.parts[0] == "outputs":
        if len(rel.parts) > 1 and rel.parts[1] in CORPUS_DIRS:
            return False
        return rel.suffix.lower() in TEXT_SUFFIXES | {".png"}
    if any(p in {"initial-script-corpus-v04", "capture-corpus", "focused-v04-fragments-before-zero-fix", "branch-capture-fragments-first-pass", "scene-inputs-v07", "scene-inputs-v09", "v17-inputs", "v18-inputs", "changed-script-inputs"} for p in rel.parts):
        return False
    return rel.suffix.lower() in TEXT_SUFFIXES or rel.name.lower().startswith(("license", "copying", "notice", "readme", "cmakelists", "makefile")) or rel.name in {".gitignore", ".gitattributes"}


start = time.time()
counts = collections.Counter()
sizes = collections.Counter()
excluded = collections.Counter()
provenance = []
for ref in sorted((ROOT / "references").iterdir()):
    if ref.is_dir() and (ref / ".git").exists():
        def git(*args):
            p = subprocess.run(["git", "-C", str(ref), *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
            return p.stdout.strip()
        remote = git("remote", "get-url", "origin")
        if "@" in remote and "://" in remote:
            remote = remote.split("://", 1)[0] + "://" + remote.split("@", 1)[1]
        provenance.append({"path": str(ref.relative_to(ROOT)).replace("\\", "/"), "origin": remote, "head": git("rev-parse", "HEAD"), "changes": git("status", "--porcelain", "-uno")})

writers = {k: zipfile.ZipFile(DEST / name, "w", zipfile.ZIP_DEFLATED, compresslevel=3, allowZip64=True) for k, name in ARCHIVES.items()}
manifest_path = DEST / "windows-file-manifest.jsonl.gz"
with gzip.open(manifest_path, "wt", encoding="utf-8") as manifest:
    for dp, ds, fs in os.walk(ROOT):
        ds.sort()
        for f in sorted(fs):
            path = Path(dp) / f
            rel = path.relative_to(ROOT)
            size = path.stat().st_size
            reason = exclusion(rel)
            record = {"path": rel.as_posix(), "bytes": size}
            if reason:
                record["excluded"] = reason
                excluded[reason] += 1
            else:
                group = scope(rel)
                digest = sha_file(path)
                record.update(sha256=digest, archive=ARCHIVES[group])
                writers[group].write(path, arcname=rel.as_posix())
                counts[group] += 1
                sizes[group] += size
                if git_include(rel, size):
                    target = GIT / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, target)
                    record["git"] = True
                    counts["git"] += 1
                    sizes["git"] += size
            manifest.write(json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n")
            if sum(counts[k] for k in ARCHIVES) % 10000 == 0 and not reason:
                print(json.dumps({"progress_files": sum(counts[k] for k in ARCHIVES), "elapsed_seconds": round(time.time()-start)}), flush=True)
for writer in writers.values():
    writer.close()
backup = {"project": "Open Amalur", "date": DATE, "source_root": str(ROOT), "private_repository": "Mokomis/open-amalur", "counts": dict(counts), "uncompressed_bytes": dict(sizes), "excluded_counts": dict(excluded), "references": provenance, "archives": []}
for name in [*ARCHIVES.values(), manifest_path.name]:
    p = DEST / name
    backup["archives"].append({"name": name, "bytes": p.stat().st_size, "sha256": sha_file(p)})
out = DEST / "archive-manifest.json"
out.write_text(json.dumps(backup, indent=2)+"\n", encoding="utf-8")
metadata = GIT / "backup-metadata"
metadata.mkdir(exist_ok=True)
shutil.copy2(out, metadata / out.name)
shutil.copy2(manifest_path, metadata / manifest_path.name)
with zipfile.ZipFile(DEST / "open-amalur-git-source-transfer.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=3) as z:
    for p in sorted(GIT.rglob("*")):
        if p.is_file():
            z.write(p, p.relative_to(GIT).as_posix())
print(json.dumps({"completed": True, "destination": str(DEST), "counts": counts, "archives": backup["archives"], "elapsed_seconds": round(time.time()-start)},ensure_ascii=True), flush=True)
