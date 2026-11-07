# rec_run.ps1 -Tag t: build the proxy, play to the save with recording on, close, report. Stops if the game dies.
param([string]$Tag='x',[int]$Hold=90)
$ErrorActionPreference='Continue'
$E='C:\Users\rwill\Documents\Opem Amalur\work\v30-engine'; $R="$E\run-rec"; $D="$E\desk.ps1"
function desk { powershell -NoProfile -ExecutionPolicy Bypass -File $D @args 2>&1 | % { "$_" } }
function intask($exe,$arg){ $a=New-ScheduledTaskAction -Execute $exe -Argument $arg; $p=New-ScheduledTaskPrincipal -UserId 'rwill' -LogonType Interactive -RunLevel Limited; Register-ScheduledTask -TaskName OA_t -Action $a -Principal $p -Force | Out-Null; Start-ScheduledTask -TaskName OA_t; Start-Sleep 4; Unregister-ScheduledTask -TaskName OA_t -Confirm:$false }
cmd /c "`"$E\proxy\build.cmd`" 2>&1" | Select-Object -Last 2 | % { "$_" }
if(-not $?){ 'BUILD FAILED'; return }
Copy-Item "$E\proxy\d3d11.dll" $R -Force; Remove-Item "$R\oa_rec" -Recurse -Force -ErrorAction SilentlyContinue
intask 'cmd.exe' "/c `"$E\run-rec.cmd`""
1..60 | % { if(Get-Process koa -ErrorAction SilentlyContinue){ return }; Start-Sleep 1 }
"koa started: " + [bool](Get-Process koa -ErrorAction SilentlyContinue)
Start-Sleep 45
"title alive: " + [bool](Get-Process koa -ErrorAction SilentlyContinue)
[void](desk -Cmd click -Keys '3000,1500'); Start-Sleep 2
[void](desk -Cmd key -Keys '{ENTER}'); Start-Sleep 10
[void](desk -Cmd key -Keys '{ENTER}'); Start-Sleep 60
[void](desk -Cmd shot -Name $Tag -Count 8)
$t0=Get-Date; $f0=[int]((Get-Content "$R\oa_rec\stats.txt" -TotalCount 1) -replace '\D','')
Start-Sleep $Hold
$f1=[int]((Get-Content "$R\oa_rec\stats.txt" -TotalCount 1) -replace '\D',''); $sec=((Get-Date)-$t0).TotalSeconds
"alive after hold: " + [bool](Get-Process koa -ErrorAction SilentlyContinue)
"fps while holding: " + [math]::Round(($f1-$f0)/$sec,1)
"--- engine"; Get-Content "$R\oa_rec\engine.txt" -ErrorAction SilentlyContinue
Select-String -Path "$R\oa_rec\resources.txt" -Pattern 'replace ' | % { $_.Line }
python "$E\callers_map.py" "$R\oa_rec\callers.txt" "$E\functions.tsv" "$E\names.tsv" "$E\render_backend_$Tag.tsv" 2>&1 | Select-Object -First 3 | % { "$_".Substring(0,[Math]::Min(170,"$_".Length)) }
intask 'conhost.exe' "--headless powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$E\closewin.ps1`" -Title Kingdoms -Out `"$E\pc\close.txt`""
1..40 | % { if(-not (Get-Process koa -ErrorAction SilentlyContinue)){ return }; Start-Sleep 1 }
"koa running: " + [bool](Get-Process koa -ErrorAction SilentlyContinue)
$s='C:\Program Files (x86)\Steam\userdata\43149042\1041720\remote\autocloud\save'; $b="$E\save-backup-20261101\save"; $n=0
Get-ChildItem $s -File | % { $x=Join-Path $b $_.Name; if(-not ((Test-Path $x) -and ((Get-FileHash -LiteralPath $_.FullName).Hash -eq (Get-FileHash -LiteralPath $x).Hash))){ $n++; "CHANGED $($_.Name) $($_.LastWriteTime)" } }; "saves changed vs backup: $n"
