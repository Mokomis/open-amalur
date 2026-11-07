from pathlib import Path
f = Path.home() / "Documents/Opem Amalur/work/v19-host/android_scene.c"
t = f.read_bytes().decode("utf-8")
old = "exploration_overlay_draw(&g->overlay,width,height,input,"
if t.count(old) != 1: raise SystemExit("overlay match %d" % t.count(old))
t = t.replace(old, "/* Test aid: adb shell setprop debug.opem.hud off hides the overlay for clean captures. */\n        {char hud_prop[PROP_VALUE_MAX]={0};if(!(__system_property_get(\"debug.opem.hud\",hud_prop)>0&&!strcmp(hud_prop,\"off\")))\n        exploration_overlay_draw(&g->overlay,width,height,input,")
t = t.replace("c->foe_ready?hud:NULL);", "c->foe_ready?hud:NULL);}", 1) if t.count("c->foe_ready?hud:NULL);") == 1 else None
if t is None: raise SystemExit("hud match")
f.write_bytes(t.encode("utf-8"))
print("patched")
