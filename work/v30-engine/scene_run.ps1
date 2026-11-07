# scene_run.ps1: load saves from the menu in rewrite and original modes and record each. Clicks only save names, never the delete column. Stops if a save changes.
$E='C:\Users\rwill\Documents\Opem Amalur\work\v30-engine'; $R="$E\run-rec"; $RunCmd="$E\run-rec.cmd"; $D="$E\desk.ps1"; $G="$E\game_ctl.ps1"
function desk { powershell -NoProfile -ExecutionPolicy Bypass -File $D @args 2>&1 | % { "$_" } }
function ctl($x){ powershell -NoProfile -ExecutionPolicy Bypass -File $G -Do $x 2>&1 | % { "$_" } }
function saves_changed { $s='C:\Program Files (x86)\Steam\userdata\43149042\1041720\remote\autocloud\save'; $b="$E\save-backup-20261101\save"; $n=0; Get-ChildItem $s -File | % { $x=Join-Path $b $_.Name; if(-not ((Test-Path $x) -and ((Get-FileHash -LiteralPath $_.FullName).Hash -eq (Get-FileHash -LiteralPath $x).Hash))){ $n++; "CHANGED $($_.Name) $($_.LastWriteTime)" | Write-Host } }; $n }
$orig=Get-Content $RunCmd -Raw
$scenes=@(@{n='dal';y=1163},@{n='ysa';y=1372},@{n='haxhi';y=1581})
try {
 foreach($sc in $scenes){ foreach($mode in 'original'){
  $tag="$($sc.n)-$mode"; "=== $tag"
  if($mode -eq 'original'){ Set-Content $RunCmd ($orig -replace 'start "" koa.exe',"set OA_NO_REPLACE=1`r`nstart `"`" koa.exe") -NoNewline } else { Set-Content $RunCmd $orig -NoNewline }
  ctl close; if(Get-Process koa -ErrorAction SilentlyContinue){ Stop-Process -Name koa -Force; Start-Sleep 3; 'forced close' }
  ctl start
  $off=[bool](Select-String -Path "$R\oa_rec\resources.txt" -Pattern 'replacements disabled'); $on=(Select-String -Path "$R\oa_rec\resources.txt" -Pattern 'replace .* applied').Count; "replacements disabled: $off, applied: $on"
  if(-not $off -or $on -ne 0){ 'STOPPING: replacements were not off'; ctl close; return }
  [void](desk -Cmd click -Keys '3000,1500'); Start-Sleep 10
  [void](desk -Cmd click -Keys '480,547'); Start-Sleep 6
  [void](desk -Cmd click -Keys "768,$($sc.y)"); Start-Sleep 4
  [void](desk -Cmd shot -Name "$tag-pick")
  [void](desk -Cmd key -Keys '{ENTER}'); Start-Sleep 80
  [void](desk -Cmd shot -Name "$tag-view")
  Start-Sleep 60
  "alive: " + [bool](Get-Process koa -ErrorAction SilentlyContinue)
  Get-Content "$R\oa_rec\engine.txt" -ErrorAction SilentlyContinue | Select-String 'draw packets|immediate' | % { "$_" }
  ctl close; if(Get-Process koa -ErrorAction SilentlyContinue){ Stop-Process -Name koa -Force; Start-Sleep 3; 'forced close' }
  Remove-Item "$E\oa_rec-$tag" -Recurse -Force -ErrorAction SilentlyContinue; Copy-Item "$R\oa_rec" "$E\oa_rec-$tag" -Recurse
  $changed=saves_changed; "saves changed vs backup: $changed"
  if($changed -ne 0){ 'STOPPING: a save changed'; return }
 } }
} finally { Set-Content $RunCmd $orig -NoNewline; "cmd restored: " + -not [bool](Select-String -Path $RunCmd -Pattern 'OA_NO_REPLACE') }
