# desk.ps1 -Cmd launch|shot|key|stop [-Name n] [-Keys k] [-Count c]: acts on the logged-in desktop through a one-shot scheduled task.
param([string]$Cmd,[string]$Name='s',[string]$Keys='',[int]$Count=1,[switch]$Inner)
$E='C:\Users\rwill\Documents\Opem Amalur\work\v30-engine'; $Out="$E\pc"; New-Item -ItemType Directory -Force $Out | Out-Null
if($Inner){
  Add-Type @'
using System.Runtime.InteropServices;
public class Dpi{[DllImport("user32")]public static extern bool SetProcessDPIAware();[DllImport("user32")]public static extern void keybd_event(byte v,byte s,uint f,System.UIntPtr e);[DllImport("user32")]public static extern uint MapVirtualKey(uint c,uint t);[DllImport("user32")]public static extern bool SetCursorPos(int x,int y);[DllImport("user32")]public static extern void mouse_event(uint f,uint x,uint y,uint d,System.UIntPtr e);}
'@
  [void][Dpi]::SetProcessDPIAware()
  Add-Type -AssemblyName System.Windows.Forms,System.Drawing
  try{
    switch($Cmd){
      'launch'{ Start-Process 'steam://rungameid/1041720' }
      'play'{
        # Tokens separated by ';': d:KEY down, u:KEY up, k:KEY:ms tap, m:dx:dy mouse move, c:N left clicks, r:N right clicks, z:ms wait, s:name screenshot
        function press($k,[uint32]$f){ $v=switch($k){'esc'{[byte]27}'space'{[byte]32}'shift'{[byte]16}'tab'{[byte]9}default{[byte][char]$k.ToUpper()}}; [Dpi]::keybd_event($v,[byte][Dpi]::MapVirtualKey($v,0),$f,[UIntPtr]::Zero) }
        foreach($t in ($Keys -split ';')){ $p=$t -split ':'
          switch($p[0]){
            'd'{ press $p[1] 0 }
            'u'{ press $p[1] 2 }
            'k'{ press $p[1] 0; Start-Sleep -Milliseconds ([int]$p[2]); press $p[1] 2 }
            'm'{ $dx=[int]$p[1]; $dy=[int]$p[2]; 1..20 | % { [Dpi]::mouse_event(1,[BitConverter]::ToUInt32([BitConverter]::GetBytes([int][math]::Truncate($dx/20)),0),[BitConverter]::ToUInt32([BitConverter]::GetBytes([int][math]::Truncate($dy/20)),0),0,[UIntPtr]::Zero); Start-Sleep -Milliseconds 25 } }
            'c'{ 1..[int]$p[1] | % { [Dpi]::mouse_event(2,0,0,0,[UIntPtr]::Zero); Start-Sleep -Milliseconds 70; [Dpi]::mouse_event(4,0,0,0,[UIntPtr]::Zero); Start-Sleep -Milliseconds 350 } }
            'r'{ 1..[int]$p[1] | % { [Dpi]::mouse_event(8,0,0,0,[UIntPtr]::Zero); Start-Sleep -Milliseconds 70; [Dpi]::mouse_event(16,0,0,0,[UIntPtr]::Zero); Start-Sleep -Milliseconds 350 } }
            'z'{ Start-Sleep -Milliseconds ([int]$p[1]) }
            's'{ $b=[System.Windows.Forms.SystemInformation]::VirtualScreen; $i=New-Object System.Drawing.Bitmap $b.Width,$b.Height; $g=[System.Drawing.Graphics]::FromImage($i); $g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size); $i.Save("$Out\$($p[1]).png",[System.Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $i.Dispose() }
          } }
      }
      'click'{ $x,$y=$Keys -split ','; [void][Dpi]::SetCursorPos([int]$x,[int]$y); Start-Sleep -Milliseconds 300; [Dpi]::mouse_event(2,0,0,0,[UIntPtr]::Zero); Start-Sleep -Milliseconds 80; [Dpi]::mouse_event(4,0,0,0,[UIntPtr]::Zero) }
      'shot'{ 1..$Count | % { $b=[System.Windows.Forms.SystemInformation]::VirtualScreen; $i=New-Object System.Drawing.Bitmap $b.Width,$b.Height; $g=[System.Drawing.Graphics]::FromImage($i); $g.CopyFromScreen($b.Location,[System.Drawing.Point]::Empty,$b.Size); $i.Save("$Out\$Name$_.png",[System.Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $i.Dispose(); Start-Sleep -Milliseconds 400 } }
      'key'{ $w=New-Object -ComObject WScript.Shell; [void]$w.AppActivate('Kingdoms of Amalur'); Start-Sleep -Milliseconds 500; [System.Windows.Forms.SendKeys]::SendWait($Keys) }
    }
    "ok $Cmd" | Set-Content "$Out\last.txt"
  }catch{ "fail $_" | Set-Content "$Out\last.txt" }
  return
}
$T='OA_desk'; Remove-Item "$Out\last.txt" -ErrorAction SilentlyContinue
$a=New-ScheduledTaskAction -Execute 'conhost.exe' -Argument "--headless powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Inner -Cmd $Cmd -Name $Name -Keys `"$Keys`" -Count $Count"
$p=New-ScheduledTaskPrincipal -UserId 'rwill' -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $T -Action $a -Principal $p -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5)) -Force | Out-Null
Start-ScheduledTask -TaskName $T
1..560 | % { if(Test-Path "$Out\last.txt"){ return }; Start-Sleep -Milliseconds 500 }
Unregister-ScheduledTask -TaskName $T -Confirm:$false
Get-Content "$Out\last.txt" -ErrorAction SilentlyContinue
