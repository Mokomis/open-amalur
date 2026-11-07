# Local worker validation — 2026-11-02

Windows execution was proven using hostname, account, CIM hardware queries and
NVIDIA tools: ROBMACHINEX, RobMachineX\rwill, Ryzen 7 7800X3D (8 cores/16 threads),
48 GB nominal system RAM, RTX 4080 SUPER 16 GB, NVIDIA driver 616.92, Windows 11
Pro build 26200. Existing SSH public-key authentication was explicitly confirmed.
Before installation, applicable Windows ancestor/project AGENTS.md locations
were checked; none were found. The new worker has its own AGENTS.md.

## Successful execution

- Strata served the selected Qwen model with actual API-reported context 16384.
- Plain inference returned the expected probe in **0.219 s** after restart.
- Native structured function calling passed the JSON argument probe.
- REA advertised 229 tools. The agent receives a five-tool read-only subset.
- Qwen selected real export and Ghidra pseudocode calls for the assigned binary.
- Each task used private REA/Ghidra session storage, exported its evidence bundle
  and closed its REA session successfully.
- The actual listener was **127.0.0.1:18180**.
- Graceful stop removed the listener, left the scheduled task Ready, and reduced
  total GPU memory to about **1,091 MiB**. Start then restored the model and 16K
  context. The scheduler has no automatic trigger and requires a logged-in user.
- Target rebinding and an unadvertised execution tool were rejected. A second
  Python process was denied the real worker lock while the first held it.
- Existing Codex config and authentication hashes, user PATH, source DLL hash
  and registered snapshot hash were unchanged. No tablet/game/save operation
  or original Ghidra DB opening was part of this setup.

## Accuracy assessment

**Broad task `20261102-161745-be5c98`: rejected for use as a behavioral summary.**
Four successful REA tool calls and valid addresses were not enough: the report
reversed a zero/nonzero failure condition and invented likely external D3D11
forwarding. Its complete raw evidence and Codex's rejection are retained.

**Narrow task `20261102-162252-6979ac`: accepted for the observed wrapper contract,
with a helper-label qualification.** Codex assigned the task through dispatch.py,
retrieved its files through the same bridge, and compared E001/E002 with source
at `C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\vk\oa_vk.c:2340`.

Verified: D3D11CreateDevice is at **0x10001000**; when the initialization guard is
zero and **FUN_10006860() returns zero**, it returns **0x80004005**. Otherwise it
returns internal device/context pointers through optional outputs, assigns
feature level **0xb000**, and returns **0**. The report copies these predicates
and assignments correctly. Its helper descriptions remain approximate: the
first call at 0x100075b0 is logging according to source; initialization inside
the guard calls 0x10006460 and 0x10006860. This is static evidence, not a game
runtime test. See each task's `codex-review.json` for the exact review.

This demonstrates useful evidence gathering and a narrow reviewed summary.
It does not establish that Qwen can autonomously solve a difficult engine
problem. Reports must remain pending review; names and plausible stories are
not evidence. Codex retains implementation and complex reasoning.

## Measured performance

| Measurement | Broad task | Narrow task |
|---|---:|---:|
| Total task, including Ghidra startup, inference and evidence close | 74.05 s | 52.06 s |
| Model-selected REA calls | 4 | 2 |
| First pseudocode call (cold private Ghidra session) | 32.16 s | 32.25 s |
| Final report request, including prompt processing | 32.41 s / 1457 tokens | 14.34 s / 665 tokens |
| Final response rate including prompt processing | 44.96 tokens/s | 46.36 tokens/s |
| Peak whole-PC physical RAM | 31,747.6 MiB | 35,491.9 MiB |
| Minimum available physical RAM | 17,009.9 MiB | 13,265.6 MiB |
| Peak whole-device VRAM | 12,669 MiB | 12,651 MiB |

The narrow run's engine log separately reports **55.3 decode tokens/s** (12.026 s
for 665 tokens), excluding prompt processing. These are short single-task
measurements, not a sustained performance benchmark. Resource samples are
approximately one second apart and cover the entire PC/GPU, including other
processes; they are not exclusive worker allocations. Minimum available RAM
was about **13.0 GiB** in the higher-memory successful run. Initial/restarted
memory usage differed; the table preserves both actual measurements.

## Resolved setup issues and current limits

- Existing REA `snapshot_path` means an input evidence snapshot. The first
  bootstrap job incorrectly supplied a new output path and failed. Corrected
  to open the assigned binary directly. That failed job is retained.
- Two 8K-context tasks overflowed after valid tool calls. Pivoted to compact
  observations plus 16K; no automatic retry of the same failing setup.
- Initial Strata expert placement left little VRAM free. Added its supported
  expert-vram cache setting; total VRAM now leaves several GiB for Windows.
- Background processes tied to SSH did not persist reliably. Replaced that
  launch mechanism with an on-demand, limited-privilege interactive scheduler
  owner. No external port, new Windows credentials or Codex auth changes.
- This is a fixed-budget static investigation agent, not an unrestricted coding
  agent or an OS sandbox. It cannot edit source, execute targets, browse the
  network or invoke arbitrary REA tools. Adding targets is a Codex-controlled
  snapshot registration step. Larger tasks need splitting; original game
  executable performance has not been established by this DLL test.
- CLI task execution stays attached to its console; inference persists
  independently. A disconnected task is not automatically resumed.

Raw outputs, the model identity, SHA256 inventory, probe, lifecycle log and
boundary verification are retained under `C:\Users\rwill\oa-worker`. Keep these
private; no model files, binaries, decompile data or credentials were uploaded
to GitHub.

Final lifecycle state: inference stopped gracefully after validation; no
listener remains on port 18180. Start on demand using the guide.
