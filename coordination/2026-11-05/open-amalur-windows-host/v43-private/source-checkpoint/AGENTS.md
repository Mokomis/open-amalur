# Open Amalur project instructions

<!-- BEGIN OPEN AMALUR LOCAL HELPER -->
## Optional local Qwen REA helper

Codex owns planning, difficult reasoning, implementation and review. Use the
local helper selectively for small static investigations or mechanical evidence
collection when that is likely to save work. Do not automatically delegate every
task: net productivity/credit savings have not been established. Its first broad
report reversed an error predicate and invented forwarding behavior; a narrower
contract report recovered the core facts correctly. Treat reports as unreviewed
evidence until Codex checks them.

### Installation and scope

- Windows host: ROBMACHINEX, account `robmachinex\rwill`.
- Authoritative project: `C:\Users\rwill\Documents\Opem Amalur`. Preserve existing
  source, outputs, original Ghidra databases, saves, signing key and credentials.
- Worker root: `C:\Users\rwill\oa-worker`.
- As installed on 2026-11-02: Strata 0.2.9 / engine 0.1.55; Qwen3.6-35B-A3B,
  UD-Q4_K_XL, 16,384 context tokens. Check current config before relying on it.
- Local endpoint: `http://127.0.0.1:18180/v1`. Keep it bound to localhost.
- SSH alias from the Mac: `open-rune-windows`; key authentication was verified
  during setup. Verify current access rather than assuming it still works.
- The on-demand scheduler owner requires `rwill` to be logged into Windows.
  Check status; do not assume inference is running. Stop it after use to release
  RAM/VRAM. If another thread is using the worker, coordinate before stopping it.
- The helper is a Python agent with real structured REA calls, not just an
  inference endpoint. It has no shell, source editor or target execution tool.

Read the worker's `AGENTS.md`, `README.md`, `VALIDATION.md` and `config.json` at
its Windows root before first use. Mac copies of the instructions, guide and
validation are in `/Users/rwillmore/Documents/Codex/2026-11-02/qwen-worker-setup`.

### Invoking it from Codex on the Mac

Use the existing dispatcher; do not replace Codex authentication or MCP settings.

```sh
helper_dispatch="/Users/rwillmore/Documents/Codex/2026-11-02/qwen-worker-setup/dispatch.py"
python3 "$helper_dispatch" status
python3 "$helper_dispatch" start --wait 150
python3 "$helper_dispatch" submit --target vulkan-layer --max-tools 2 --question 'YOUR SMALL, PRECISE INVESTIGATION QUESTION'
python3 "$helper_dispatch" run-next
python3 "$helper_dispatch" result TASK_ID --json
python3 "$helper_dispatch" fetch TASK_ID
python3 "$helper_dispatch" stop --wait 30
```

Capture the ID from `submit` and replace `TASK_ID` accordingly. `run-next`
processes the oldest unstarted queued job; confirm its returned task ID and
check for an existing investigation before consuming another thread's queue.
Keep the console/SSH command alive until completion. There is no unattended
worker daemon or automatic task resumption. Fetched evidence goes under
`/Users/rwillmore/Documents/Codex/2026-11-02/qwen-worker-setup/results/TASK_ID/`.

### Invoking it directly on Windows

```powershell
$helperRoot = 'C:\Users\rwill\oa-worker'
$helperPython = 'C:\Users\rwill\AppData\Local\Programs\Python\Python312\python.exe'
& $helperPython "$helperRoot\scripts\control.py" status
& $helperPython "$helperRoot\scripts\control.py" start --wait 150
& $helperPython "$helperRoot\scripts\worker.py" submit --target vulkan-layer --max-tools 2 --question 'YOUR SMALL, PRECISE INVESTIGATION QUESTION'
& $helperPython "$helperRoot\scripts\worker.py" run-next
& $helperPython "$helperRoot\scripts\worker.py" result TASK_ID --json
& $helperPython "$helperRoot\scripts\control.py" stop --wait 30
```

### Task boundaries and evidence review

- `vulkan-layer` is the Open Amalur target registered during setup: a copy of
  our own `work\v30-engine\vk\d3d11.dll`. The game executable is not automatically
  registered. Inspect current config; other projects may have registered their
  own targets and queued work. Preserve those entries/jobs. Register another authorized binary only
  using a separate read-only snapshot, recorded SHA256 and separate target entry
  as described in the guide; preserve existing registrations.
- Give one specific question and request exact addresses, branch predicates,
  output assignments, E-number citations and uncertainties. Prefer two tool
  calls for simple contracts; four is the configured maximum. Split larger work.
- Available model tools: native exports, procedure search, pseudocode, callees
  and function summaries. Do not add execution/edit tools for this workflow.
- Each job uses private REA/Ghidra session storage and the worker's real OS lock.
  Never repoint it at the original analysis database. Do not bypass the lock or
  run competing investigations. Coding changes remain Codex's responsibility;
  future concurrent edits require isolated worktrees or explicit file ownership.
- Read `status.json`, `report.md` and the cited raw `E###.json` files. Check
  addresses, zero/nonzero branch polarity and pointer assignments yourself.
  Inspect saved evidence when the model received a truncated preview. A state
  of `completed_pending_codex_review` confirms execution, not correctness.
- Every job's reports, raw evidence, model replies, evidence bundle and resource
  metrics are in `C:\Users\rwill\oa-worker\results\TASK_ID`. Record Codex's review
  beside the result before using findings for implementation. Separate static
  observations from inferences and runtime claims.
- Do not repeatedly retry unchanged failures. Narrow the task or handle it with
  Codex/REA. If access fails, identify the exact blocker; do not reinstall or
  reconfigure functioning tools just to recreate this setup.
<!-- END OPEN AMALUR LOCAL HELPER -->
