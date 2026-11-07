# load_save.ps1 -Row y: start the recording build and load one save. Clicks only the name column.
param([int]$Row=1163)
$E='C:\Users\rwill\Documents\Opem Amalur\work\v30-engine'; $D="$E\desk.ps1"; $G="$E\game_ctl.ps1"
function desk { powershell -NoProfile -ExecutionPolicy Bypass -File $D @args 2>&1 | % { "$_" } }
function ctl($x){ powershell -NoProfile -ExecutionPolicy Bypass -File $G -Do $x 2>&1 | % { "$_" } }
ctl close; if(Get-Process koa -ErrorAction SilentlyContinue){ Stop-Process -Name koa -Force; Start-Sleep 3; 'forced close' }
ctl start
[void](desk -Cmd click -Keys '3000,1500'); Start-Sleep 10
[void](desk -Cmd click -Keys '480,547'); Start-Sleep 6
[void](desk -Cmd click -Keys "768,$Row"); Start-Sleep 4
[void](desk -Cmd key -Keys '{ENTER}'); Start-Sleep 60
"loaded, alive: " + [bool](Get-Process koa -ErrorAction SilentlyContinue)
