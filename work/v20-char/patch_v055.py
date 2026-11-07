from pathlib import Path
p=Path.home()/"Documents/Opem Amalur/work/v19-host/android_scene.c";t=p.read_text(encoding="utf-8")
a='prof.heading=prop_int("debug.opem.heading",0);'
assert a in t
if "debug.opem.hide" not in t:
    t=t.replace(a,a+'{extern int oa_stream_hide;oa_stream_hide=prop_int("debug.opem.hide",0);}')
p.write_text(t,encoding="utf-8",newline="\n");print("ok")
