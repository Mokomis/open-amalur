#!/usr/bin/env python3
"""compile_all.py <clang> <out dir> <jobs>: compile every translated chunk for ARM64 and report what failed."""
import concurrent.futures as cf, glob, os, subprocess, sys, time

clang, out, jobs = sys.argv[1], sys.argv[2], int(sys.argv[3])
files = sorted(glob.glob(os.path.join(out, "koa_*.c")))


def one(path):
    t = time.time()
    r = subprocess.run([clang, "--target=aarch64-linux-android29", "-O1", "-w", "-ferror-limit=5", "-fbracket-depth=4096", "-c", path, "-o", path[:-2] + ".o"], capture_output=True, text=True)
    return path, r.returncode, r.stderr[:1500], time.time() - t


t0 = time.time()
ok = bad = 0
slow = 0.0
errors = []
with cf.ThreadPoolExecutor(jobs) as ex:
    for i, (p, rc, err, sec) in enumerate(ex.map(one, files)):
        slow = max(slow, sec)
        if rc:
            bad += 1
            errors.append((os.path.basename(p), err))
        else:
            ok += 1
        if (i + 1) % 10 == 0:
            print(f"{i + 1}/{len(files)} done, ok {ok}, failed {bad}, {round(time.time() - t0)} s", flush=True)
size = sum(os.path.getsize(f) for f in glob.glob(os.path.join(out, "koa_*.o")))
print(f"COMPILE chunks {len(files)} ok {ok} failed {bad} seconds {round(time.time() - t0)} slowest {round(slow)} s objects {round(size / 1e6, 1)} MB")
for n, e in errors[:6]:
    print("FAIL", n, e[:700])
