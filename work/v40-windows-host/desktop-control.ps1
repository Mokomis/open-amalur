param([string]$Action='close',[int]$Key=0,[int]$Down=0,[switch]$Inner)
$ErrorActionPreference='Stop'
trap { $_ | Out-File -Encoding utf8 (Join-Path $PSScriptRoot 'control-error.txt'); exit 1 }
if($Inner){
 Add-Type @'
using System;using System.Runtime.InteropServices;public class OAWindow{[DllImport("user32.dll",CharSet=CharSet.Ansi)]public static extern IntPtr FindWindow(string c,string t);[DllImport("user32.dll")]public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);}
'@
 $h=[OAWindow]::FindWindow('OpenAmalurCustomWindows',$null)
 if($h -eq [IntPtr]::Zero){throw 'Custom engine window not found'}
 if($Action -eq 'close'){[void][OAWindow]::PostMessage($h,16,[IntPtr]::Zero,[IntPtr]::Zero)}
 elseif($Action -eq 'key'){[void][OAWindow]::PostMessage($h,$(if($Down){256}else{257}),[IntPtr]$Key,[IntPtr]::Zero)}
 return
}
$t='OA_CustomControl_v40'
$a=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Inner -Action $Action -Key $Key -Down $Down"
$p=New-ScheduledTaskPrincipal -UserId 'rwill' -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $t -Action $a -Principal $p -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries) -Force | Out-Null
Start-ScheduledTask -TaskName $t
