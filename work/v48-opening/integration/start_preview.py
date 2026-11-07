from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[3];V=P/'work/v48-opening/integration';W=P/'work/v40-windows-host'
existing=subprocess.check_output(['tasklist','/FI','IMAGENAME eq open-amalur-windows.exe','/FO','CSV','/NH'],text=True)
if 'open-amalur-windows.exe' in existing.lower():raise SystemExit('Preserve running preview; close it before another launch.')
argv=[str(W/'build/open-amalur-windows.exe'),'--assets',str(V/'probe-preview-closed-container'),'--user-data',str(V/'user-data'),'--town','--capture',str(V/'closed-container-first-room-auto.bmp'),'--capture-frame','360']
process=subprocess.Popen(argv,cwd=W,creationflags=subprocess.CREATE_NO_WINDOW)
(V/'preview.pid').write_text(str(process.pid)+'\n')
