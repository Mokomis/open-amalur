from pathlib import Path
import subprocess
R=Path(r'C:\Users\rwill\Documents\Opem Amalur')
V=R/'work/v50-character-complete/live-integration'
W=R/'work/v40-windows-host'
existing=subprocess.check_output(['tasklist','/FI','IMAGENAME eq open-amalur-windows.exe','/FO','CSV','/NH'],text=True)
if 'open-amalur-windows.exe' in existing.lower():raise SystemExit('Preserve running preview')
argv=[str(W/'build/open-amalur-windows.exe'),'--assets',str(R/'work/v48-opening/integration/probe-preview-closed-container'),'--user-data',str(V/'live-user-data-20261106'),'--capture',str(V/'creator-check-auto.bmp'),'--capture-frame','360']
p=subprocess.Popen(argv,cwd=W,creationflags=subprocess.CREATE_NO_WINDOW)
(V/'creator-check.pid').write_text(str(p.pid)+'\n')
