import shlex,subprocess
adb=['/opt/homebrew/bin/adb','-s','99cc517a'];pkg='org.openamalur.nativebenchmark';base='/data/user/0/'+pkg+'/files'
def shell(c):return subprocess.run(adb+['shell',c],check=True)
shell('input keyevent KEYCODE_WAKEUP');shell('wm dismiss-keyguard');shell('am force-stop '+pkg)
args=['--remove-unsupported','--memory-translation','rebind','--opcd','--pause-frame','1','--log-file',base+'/visible-scene.log',base+'/dalentarth.gfxr']
shell(shlex.join(['am','start','-n',pkg+'/android.app.NativeActivity','--es','args',shlex.join(args)]))
