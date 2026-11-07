$act=New-ScheduledTaskAction -Execute 'C:\Users\rwill\AppData\Local\Programs\Python\Python312\pythonw.exe' -Argument '"C:\Users\rwill\Documents\Opem Amalur\work\v40-windows-host\start.py" --scene reference --user-data "C:\Users\rwill\Documents\Opem Amalur\work\v46-canopy\reference-data"'
$who=New-ScheduledTaskPrincipal -UserId 'rwill' -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName OA_V46_Canopy_Reference -Action $act -Principal $who -Force | Out-Null
Start-ScheduledTask -TaskName OA_V46_Canopy_Reference
