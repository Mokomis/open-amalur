# Open Amalur: local Qwen REA worker

Installed and tested on ROBMACHINEX on 2026-11-02. Codex owns planning,
implementation and review. One local Qwen agent performs bounded read-only
investigations and saves its evidence. The worker is a Python agent loop, not
just an inference server: Qwen selects structured REA tool calls, receives their
observations, and writes a report for Codex to review.

## Locations and versions

| Component | Version / location |
|---|---|
| Worker root | `C:\Users\rwill\oa-worker` |
| Authoritative project, preserved | `C:\Users\rwill\Documents\Opem Amalur` (not a Git checkout) |
| New Strata terminal/app | 0.2.9; terminal/control build 0.1.55; `oa-worker\strata\terminal\current\bin\strata.cmd` |
| New inference engine | Strata 0.1.55, CUDA 13, source `f-029-rel`, commit `99866a47a2b8` |
| New model | Qwen3.6-35B-A3B, Unsloth **UD-Q4_K_XL**, `models\models\qwen36-UD-Q4_K_XL\Qwen3.6-35B-A3B-UD-Q4_K_XL.gguf`, 22,853,663,008 bytes |
| Model endpoint | `http://127.0.0.1:18180/v1`; API ID `qwen3.6-35b-a3b-ud-q4_k_xl` |
| Reused Python | 3.12.10, `C:\Users\rwill\AppData\Local\Programs\Python\Python312\python.exe` |
| New Strata private Python | 3.12.15, inside the isolated Strata installation |
| Reused Node/npm | Node 26.13.0 / npm 11.20.0, `C:\Program Files\nodejs\node.exe` |
| Reused REA | 6.8.0, project `tools\rea\node_modules\rea-agents\scripts\rea.mjs` |
| Reused Ghidra | 12.1.4 PUBLIC, project `tools\ghidra_12.1.4_PUBLIC` |
| Reused Java | Temurin 21.0.13+9, project `tools\jdk-21.0.13+9` |
| Reused Git | 2.56.0.windows.3, `C:\Program Files\Git\cmd\git.exe` |
| Existing Codex CLI, preserved | 0.166.0-alpha.5.1, `C:\Users\rwill\AppData\Local\OpenAI\Codex\bin\22cfb1d302613eae\codex.exe` |

Strata also creates its own new component/launch/install folders in
`C:\Users\rwill\AppData\Local\Strata` and settings/profiles in
`C:\Users\rwill\AppData\Roaming\Strata`. The engine executable is in
`AppData\Local\Strata\components\engine\0.1.55-windows-x86_64-cuda-cuda13`.
No global PATH edit, Codex authentication edit or Codex MCP reconfiguration was
needed. Existing Codex was found in its bundled location rather than PATH. No
other checked agent command (Claude, Qwen, OpenCode, Aider, Goose or Gemini) was
on PATH. The default npm-global directory did not exist; npm reported ENOENT,
so this does not establish the absence of agents installed elsewhere. No Ollama, LM Studio, llama.cpp, Qwen-Agent or extra cloud agent was
installed. No existing local model/runtime was found in the checked standard
locations; this was not an exhaustive scan of every disk.

The live host has a Ryzen 7 7800X3D, 48 GB nominal RAM and RTX 4080 SUPER
16 GB; NVIDIA driver 616.92. Initial available RAM was about 39 GiB and initial
free C: space about 571.5 GB. After setup C: had about 547.3 GB free. Exact
hardware, model hash and versions are in `inventory-final.json`.

The real engine sources, `work\v30-engine\decomp`, names/classes/functions TSVs,
Ghidra database, existing `show_fn.py`, HANDOFF.md, PLAN.md and CURRENT_STATE.txt
remain in the authoritative project. The sibling
`C:\Users\rwill\Documents\Open Amalur Backups` folder was also found and preserved;
neither top-level folder is a Git checkout. This worker does not open its live Ghidra
database. The frozen custom GLES engine remains frozen. The tablet and saves
were not used for setup.

## Why this configuration

Official Strata documentation lists a Windows/CUDA Qwen3.6 pack and its
OpenAI-compatible structured tool interface. Both work on this PC. The chosen
35B model is an MoE model with about 3B active parameters; its supported 4-bit
pack fits the available host RAM while preserving room for Ghidra. Larger
quantizations and the much larger alternative coder packs were unnecessary.
This selection follows supported packs and measured memory, not parameter
count alone.

The runtime uses **16,384 context tokens**, one request at a time, vision off,
and `expert-vram=3.5` GiB for the routed-expert cache. That cache limit is not a
limit on total VRAM. The final measured total device use was about 12.4 GiB.
The initial 8K setting overflowed twice on multi-function tool replies; it was
replaced with 16K and compact tool observations. The full evidence is retained.
There is no silent history dropping or automatic context compaction: excessive
context or repeated identical calls stops the job. Split larger questions into
separate investigations. Output is capped at 1,800 tokens per model turn; at
most four REA calls per task, optionally fewer; normal task wall-time budget
900 seconds checked between operations (not a hard process-kill deadline).

Official sources consulted:
- https://github.com/Niko1221/Strata/blob/main/docs/MODELS.md
- https://github.com/Niko1221/Strata/blob/main/docs/QWEN36.md
- https://github.com/Niko1221/Strata/blob/main/docs/TERMINAL_LAUNCH.md
- https://github.com/Niko1221/Strata/blob/main/docs/AI_REFERENCE.md
- https://github.com/Niko1221/Strata/blob/99866a47a2b8/src/qwen35/q36_engine.cu
- https://huggingface.co/Qwen/Qwen3.6-35B-A3B
- https://github.com/QwenLM/Qwen3/blob/main/docs/source/framework/function_call.md

## Windows: start, assign, retrieve and stop

Run from PowerShell, including Codex's shell. These commands use the existing
Python directly; no activation or cloud login is needed.

```powershell
$w = 'C:\Users\rwill\oa-worker'
$py = 'C:\Users\rwill\AppData\Local\Programs\Python\Python312\python.exe'
& $py "$w\scripts\control.py" start --wait 150
& $py "$w\scripts\worker.py" submit --target vulkan-layer --max-tools 2 --question 'Locate D3D11CreateDevice. Read its wrapper pseudocode and report the exact error predicate and output assignments, with E-number evidence citations. Do not analyze callees or speculate.'
& $py "$w\scripts\worker.py" run-next
& $py "$w\scripts\worker.py" result '<ID printed by submit>'
& $py "$w\scripts\control.py" status
& $py "$w\scripts\control.py" stop --wait 30
```

`submit` queues a JSON task; `run-next` processes the oldest unstarted task and
returns its ID, state, paths and metrics. Keep its console/SSH session alive
until it finishes. It does not silently retry failed jobs. Submit a narrower
new task after inspecting failures. Run `result ID --json` for structured
retrieval, including the report. The inference service and an investigation
have separate lifetimes; stopping inference during a task will fail that task.

The on-demand scheduled task `OpenAmalur-Qwen-Local-20261102` owns the service,
so it survives SSH disconnection. It runs as the existing user with limited
privileges, has no startup/time/logon triggers, and **requires that rwill is
logged into Windows**. Start/stop commands are idempotent in the ordinary
running/stopped states. Do not change its logon/security settings to work around
a logged-out PC. Start may take tens of seconds while loading the model.
`runtime-status.json` and `runtime-service.log` retain lifecycle evidence;
`control.py status` also checks the actual endpoint, model and context.

## Codex on the Mac: same queue, no manual copy/paste

Dispatcher location:
`/Users/rwillmore/Documents/Codex/2026-11-02/qwen-worker-setup/dispatch.py`

```sh
python3 /Users/rwillmore/Documents/Codex/2026-11-02/qwen-worker-setup/dispatch.py start --wait 150
python3 /Users/rwillmore/Documents/Codex/2026-11-02/qwen-worker-setup/dispatch.py submit --max-tools 2 --question 'Locate D3D11CreateDevice and report its exact error predicate with REA evidence.'
python3 /Users/rwillmore/Documents/Codex/2026-11-02/qwen-worker-setup/dispatch.py run-next
python3 /Users/rwillmore/Documents/Codex/2026-11-02/qwen-worker-setup/dispatch.py result TASK_ID --json
python3 /Users/rwillmore/Documents/Codex/2026-11-02/qwen-worker-setup/dispatch.py fetch TASK_ID
python3 /Users/rwillmore/Documents/Codex/2026-11-02/qwen-worker-setup/dispatch.py stop --wait 30
```

`fetch` copies a task's reports, raw tool evidence and metrics into the local
`results/TASK_ID` directory for Codex review. It does not copy the binary or
model. The dispatcher uses the existing `open-rune-windows` SSH alias with
BatchMode/public-key authentication, verified against ROBMACHINEX at
192.168.68.59 during setup. It passes arguments as encoded structured data,
without interpolating the question into a shell command. The inference port
is never forwarded or exposed outside Windows localhost.

## Evidence and isolation

The registered `vulkan-layer` target is a read-only immutable snapshot of the
project's own 202,240-byte `work\v30-engine\vk\d3d11.dll`. Both source and snapshot
SHA256 were checked. It is analyzed statically, never loaded or executed.

Every task gets `results\TASK_ID\` containing:
- `task.json`, `status.json`, `report.md` (if completed), model replies and conversation;
- `E001.json`, etc.: original unmodified REA tool replies with evidence IDs;
- `evidence-bundle.json` and REA startup/close logs;
- `resources.jsonl`: approximately one-second whole-PC RAM and whole-device VRAM samples.

Only five read-only tools are advertised to Qwen: native exports, procedure
search, pseudocode, callees and function summary. The host fixes the target
path and rejects target changes and unadvertised tools. Qwen has no shell,
editor or external network tool. This is an application boundary, **not an OS
security sandbox for arbitrary hostile binaries**. Only registered authorized
targets should be used.

REA reuses the installed decompiler, but creates a private session/project
under `oa-worker\analysis` via child-only TEMP/TMP, not the original project DB.
A real Windows file lock prevents two worker investigations from overlapping.
This lock does not coordinate unrelated REA/Ghidra clients; private DBs avoid
their shared-database risk. The agent cannot edit source, so no concurrent edit
worktree is needed. Future coding capability would require its own checkout
or clearly assigned files before enabling write tools.

Register additional targets only after copying an authorized binary into
`targets`, making it read-only, recording its full SHA256 and adding its entry
to `config.json`. Large game executables may need more Ghidra time/resources;
this setup's successful smoke test does not establish whole-game analysis
throughput. Do not repoint it at the original live database.

## Verification and interpretation

See `VALIDATION.md` and `results\boundary-verification.json` for the actual
results. Completed tasks initially say `completed_pending_codex_review`.
Successful tool execution does not establish an accurate report. Codex must
read the cited raw evidence, check addresses, branch polarity and assignments,
and separate static facts from runtime claims before using the findings.

The initial broad report was rejected for a reversed error condition and
unsupported forwarding guesses. It is retained with its evidence. The narrower
contract investigation is reviewed separately. Do not use unreviewed output
to patch the engine. Treat this worker as an evidence-gathering assistant;
complex architecture and game-behavior conclusions remain Codex's work.

Stop the runtime before playing a GPU-heavy game to reclaim its VRAM. This
setup establishes resource headroom for its tested DLL/Ghidra task; it does not
promise comfortable simultaneous gaming plus inference.

At the end of setup, inference was **stopped** to release RAM/VRAM. Start it
on demand using the commands above. The worker files, model and queue remain.
