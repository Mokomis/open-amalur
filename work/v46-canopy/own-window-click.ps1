param([int]$X,[int]$Y,[switch]$Inner)
$ErrorActionPreference='Stop'
trap { $_ | Out-File -Encoding utf8 "$PSScriptRoot/click-error.txt";exit 1 }
if($Inner){
 Add-Type @'
using System;using System.Runtime.InteropServices;public class OAClick{[DllImport("user32.dll",CharSet=CharSet.Ansi)]public static extern IntPtr FindWindow(string c,string t);[DllImport("user32.dll")]public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);}
'@
 $h=[OAClick]::FindWindow('OpenAmalurCustomWindows',$null)
 if($h -eq [IntPtr]::Zero){throw 'Own custom engine window not found'}
 if($X -lt 0 -or $X -ge 1536 -or $Y -lt 0 -or $Y -ge 864){throw 'Outside verified client image'}
 $point=[IntPtr](($Y -shl 16) -bor $X)
 [void][OAClick]::PostMessage($h,513,[IntPtr]1,$point)
 Start-Sleep -Milliseconds 100
 [void][OAClick]::PostMessage($h,514,[IntPtr]0,$point)
 'Own-window click consumed' | Set-Content -Encoding utf8 "$PSScriptRoot/click-result.txt"
 return
}
$act=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Inner -X $X -Y $Y"
$who=New-ScheduledTaskPrincipal -UserId 'rwill' -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName OA_V46_OwnWindowClick -Action $act -Principal $who -Force | Out-Null
Start-ScheduledTask -TaskName OA_V46_OwnWindowClick
