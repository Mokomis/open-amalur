param([string]$Title,[string]$Out)
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;using System.Text;using System.Runtime.InteropServices;
public class X{public delegate bool P(IntPtr h,IntPtr l);[DllImport("user32")]public static extern bool EnumWindows(P p,IntPtr l);[DllImport("user32")]public static extern bool IsWindowVisible(IntPtr h);[DllImport("user32",CharSet=CharSet.Unicode)]public static extern int GetWindowText(IntPtr h,StringBuilder s,int n);[DllImport("user32")]public static extern bool GetWindowRect(IntPtr h,out R r);[DllImport("user32")]public static extern bool PrintWindow(IntPtr h,IntPtr d,uint f);[DllImport("user32")]public static extern bool SetProcessDPIAware();public struct R{public int a,b,c,d;}}
'@
[void][X]::SetProcessDPIAware()
$script:hit=[IntPtr]::Zero
[X]::EnumWindows({param($h,$x) if([X]::IsWindowVisible($h)){$s=New-Object Text.StringBuilder 200;[void][X]::GetWindowText($h,$s,200);if($s.ToString() -like "$Title*"){$script:hit=$h}};$true},[IntPtr]::Zero)|Out-Null
if($script:hit -eq [IntPtr]::Zero){"none"|Set-Content "$Out.txt";return}
$r=New-Object X+R;[void][X]::GetWindowRect($script:hit,[ref]$r);$w=$r.c-$r.a;$h=$r.d-$r.b
$b=New-Object Drawing.Bitmap $w,$h;$g=[Drawing.Graphics]::FromImage($b);$d=$g.GetHdc();$ok=[X]::PrintWindow($script:hit,$d,2);$g.ReleaseHdc($d);$b.Save("$Out.png",[Drawing.Imaging.ImageFormat]::Png);"$ok $w x $h"|Set-Content "$Out.txt"
