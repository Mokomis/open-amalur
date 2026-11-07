$O='C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\pc\wins.txt'
Add-Type @'
using System;using System.Text;using System.Runtime.InteropServices;
public class W{public delegate bool P(IntPtr h,IntPtr l);[DllImport("user32")]public static extern bool EnumWindows(P p,IntPtr l);[DllImport("user32")]public static extern bool IsWindowVisible(IntPtr h);[DllImport("user32",CharSet=CharSet.Unicode)]public static extern int GetWindowText(IntPtr h,StringBuilder s,int n);[DllImport("user32")]public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);[DllImport("user32")]public static extern bool GetWindowRect(IntPtr h,out R r);public struct R{public int a,b,c,d;}}
'@
$l=New-Object System.Collections.ArrayList
[W]::EnumWindows({param($h,$x) if([W]::IsWindowVisible($h)){$s=New-Object Text.StringBuilder 200;[void][W]::GetWindowText($h,$s,200);$p=0;[void][W]::GetWindowThreadProcessId($h,[ref]$p);$r=New-Object W+R;[void][W]::GetWindowRect($h,[ref]$r);if($s.Length){[void]$l.Add("$((Get-Process -Id $p).ProcessName) | $s | $($r.a),$($r.b) $($r.c-$r.a)x$($r.d-$r.b)")}};$true},[IntPtr]::Zero)|Out-Null
$l | Set-Content $O
