"""Inside the native guest: one held F10, always released. Inspect screen first."""
import ctypes as c
import os
import time
os.setgid(10307)
os.setuid(10307)
x = c.CDLL('libX11.so.6')
t = c.CDLL('libXtst.so.6')
x.XOpenDisplay.argtypes = [c.c_char_p]
x.XOpenDisplay.restype = c.c_void_p
x.XKeysymToKeycode.argtypes = [c.c_void_p, c.c_ulong]
x.XKeysymToKeycode.restype = c.c_ubyte
x.XSync.argtypes = [c.c_void_p, c.c_int]
x.XCloseDisplay.argtypes = [c.c_void_p]
t.XTestFakeKeyEvent.argtypes = [c.c_void_p, c.c_uint, c.c_int, c.c_ulong]
d = x.XOpenDisplay(b':1')
if not d:
    raise SystemExit('Game X display unavailable; no key sent')
code = x.XKeysymToKeycode(d, 0xffc7)  # XK_F10
try:
    if not code:
        raise SystemExit('F10 keycode unavailable')
    t.XTestFakeKeyEvent(d, code, 1, 0)
    x.XSync(d, 0)
    time.sleep(0.5)
finally:
    if code:
        t.XTestFakeKeyEvent(d, code, 0, 0)
        x.XSync(d, 0)
    x.XCloseDisplay(d)
print('F10 pressed for 500 ms and released; verify capture log and file.')
