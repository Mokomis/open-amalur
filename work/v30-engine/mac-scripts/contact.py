import sys; sys.path.insert(0, sys.argv[1]); import sheet
d=sys.argv[2]; names=sys.argv[4:]
W,H=1200,900; out=bytearray((40,44,52,255)*(W*H)); cx=cy=rowh=0
for n in names:
    w,h,x=sheet.rd(f"{d}/{n}.png"); s=max(1,max(w,h)//400)
    tw,th=w//s,h//s
    if cx+tw>W: cx=0; cy+=rowh+8; rowh=0
    if cy+th>H: break
    for yy in range(th):
        for xx in range(tw):
            p=(yy*s*w+xx*s)*4; a=x[p+3]; q=((cy+yy)*W+cx+xx)*4
            for e in range(3): out[q+e]=(x[p+e]*a+out[q+e]*(255-a))//255
    cx+=tw+8; rowh=max(rowh,th)
sheet.wr(sys.argv[3],W,H,out)
