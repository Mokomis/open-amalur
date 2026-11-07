param([string]$Title,[string]$Out)
Add-Type @'
using System;using System.Text;using System.Runtime.InteropServices;
public class Y{public delegate bool P(IntPtr h,IntPtr l);[DllImport("user32")]public static extern bool EnumWindows(P p,IntPtr l);[DllImport("user32")]public static extern bool IsWindowVisible(IntPtr h);[DllImport("user32",CharSet=CharSet.Unicode)]public static extern int GetWindowText(IntPtr h,StringBuilder s,int n);[DllImport("user32")]public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);}
'@
$script:n=0
[Y]::EnumWindows({param($h,$x) if([Y]::IsWindowVisible($h)){$s=New-Object Text.StringBuilder 200;[void][Y]::GetWindowText($h,$s,200);if($s.ToString() -like "$Title*"){[void][Y]::PostMessage($h,0x10,[IntPtr]::Zero,[IntPtr]::Zero);$script:n++}};$true},[IntPtr]::Zero)|Out-Null
"closed $script:n"|Set-Content $Out
