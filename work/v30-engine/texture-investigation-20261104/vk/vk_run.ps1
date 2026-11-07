# vk_run.ps1 -Tag t -Wait s: build and start the game on our Vulkan layer, capture the screen, leave it running.
param([string]$Tag='v',[int]$Wait=40)
$E='C:\Users\rwill\Documents\Opem Amalur\work\v30-engine'; $R="$E\run-vk"; $D="$E\desk.ps1"; $G='C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning'
function desk { powershell -NoProfile -ExecutionPolicy Bypass -File $D @args 2>&1 | % { "$_" } }
function intask($exe,$arg){ $a=New-ScheduledTaskAction -Execute $exe -Argument $arg; $p=New-ScheduledTaskPrincipal -UserId 'rwill' -LogonType Interactive -RunLevel Limited; Register-ScheduledTask -TaskName OA_t -Action $a -Principal $p -Force | Out-Null; Start-ScheduledTask -TaskName OA_t; Start-Sleep 4; Unregister-ScheduledTask -TaskName OA_t -Confirm:$false }
if(Get-Process koa -ErrorAction SilentlyContinue){ intask 'conhost.exe' "--headless powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$E\closewin.ps1`" -Title Kingdoms -Out `"$E\pc\close.txt`""; 1..15 | % { if(-not (Get-Process koa -ErrorAction SilentlyContinue)){ return }; Start-Sleep 1 }; Stop-Process -Name koa -Force -ErrorAction SilentlyContinue; Start-Sleep 2 }
$buildout=cmd /c "`"$E\vk\build.cmd`" 2>&1"; $errs=$buildout | Select-String 'error'; if($errs){ $errs | Select-Object -First 20 | % { "$_" }; return }
New-Item -ItemType Directory -Force $R | Out-Null
foreach($n in 'koa.exe','binkw32.dll','libeay32.dll','ssleay32.dll','steam_api.dll','dualsense.padcfg','dualshock4.padcfg','switchprocon.padcfg'){ if(-not (Test-Path "$R\$n")){ Copy-Item "$G\$n" $R -Force } }
foreach($sub in 'data','data_1278260','padconfig','modding'){ if(-not (Test-Path "$R\$sub")){ cmd /c mklink /J "$R\$sub" "$G\$sub" | Out-Null } }
Copy-Item "$E\vk\d3d11.dll" $R -Force; Set-Content "$R\steam_appid.txt" '1041720' -NoNewline
Set-Content "$E\run-vk.cmd" "@echo off`r`ncd /d `"$R`"`r`nset SteamAppId=1041720`r`nset SteamGameId=1041720`r`nstart `"`" koa.exe`r`n"
intask 'cmd.exe' "/c `"$E\run-vk.cmd`""
Start-Sleep $Wait
"alive: " + [bool](Get-Process koa -ErrorAction SilentlyContinue)
Get-Process koa -ErrorAction SilentlyContinue | % { "mem $([math]::Round($_.WorkingSet64/1MB)) MB" }
"shot: " + (desk -Cmd shot -Name $Tag)
"--- log"; Get-Content "$R\oa_vk.log" -ErrorAction SilentlyContinue | Select-Object -Last 40
"--- crash"; Get-WinEvent -FilterHashtable @{LogName='Application';StartTime=(Get-Date).AddMinutes(-3);Id=1000} -ErrorAction SilentlyContinue | Where-Object { $_.Message -match 'koa' } | Select-Object -First 1 | % { ($_.Message -replace "`r?`n",' ').Substring(0,300) }
"--- game log"; Get-Content "$R\Kingdoms of Amalur_ Re-Reckoning.log" -Tail 6 -ErrorAction SilentlyContinue | % { $_.Substring(0,[Math]::Min(120,$_.Length)) }
