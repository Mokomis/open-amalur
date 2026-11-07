#!/usr/bin/env python3
"""img_diff.py <a.png> <b.png>: share of pixels differing, whole image and four background regions away from the character and HUD."""
import importlib.util,sys
spec=importlib.util.spec_from_file_location("m",sys.argv[0].replace("img_diff.py","flash_lib.py"))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
w,h,a=m.luma(sys.argv[1]);_,_,b=m.luma(sys.argv[2])
def pct(x0,x1,y0,y1,t=16):
    n=d=0
    for y in range(y0,y1):
        for x in range(x0,x1):
            n+=1;d+=abs(a[y][x]-b[y][x])>t
    return 100*d/n
print(f"whole {pct(0,w,0,h):.1f}% left {pct(0,w//4,h//4,h*3//4):.1f}% right {pct(w*3//4,w,h//3,h*3//4):.1f}% top {pct(w//3,w*2//3,0,h//5):.1f}%")
