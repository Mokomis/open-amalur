import struct,sys,zlib
sys.path.insert(0,sys.argv[1]);import sheet
def load(font,ntx):
    b=open(font,'rb').read()
    E=b.find(bytes.fromhex('0000000008000000'),0x400)
    k=0
    while True:
        o=E-18*(k+1)
        yo,q,x0,x1,y0,y1,pg,adv,xo=struct.unpack_from('<hHHHHHHHh',b,o)
        if not(0<=x0<x1<=512 and 0<=y0<y1<=512 and pg==0 and -200<yo<50): break
        k+=1
    st=E-18*k
    m=[struct.unpack_from('<H',b,0x94+2*i)[0] for i in range((st-0x94)//2)]
    print(font,'records',k,'start',hex(st),'map entries',len(m),'max',max(v for v in m if v!=0xffff))
    g={}
    for cp,v in enumerate(m):
        if v<k:
            g[cp]=struct.unpack_from('<hHHHHHHHh',b,st+18*v)
    return g,open(ntx,'rb').read()[80:80+262144]
g,t=load(sys.argv[2],sys.argv[3])
for ch in ' AIMaim.,g':
    print(repr(ch),g.get(ord(ch)))
TH=float(sys.argv[4]) if len(sys.argv)>4 else 110
W,H=1000,150; out=bytearray((20,24,26,255)*(W*H))
def draw(s,x,base,scale):
    for ch in s:
        r=g.get(ord(ch))
        if not r: x+=10*scale;continue
        yo,q,x0,x1,y0,y1,pg,adv,xo=r
        gw,gh=x1-x0,y1-y0
        for py in range(int(gh*scale)):
            for px in range(int(gw*scale)):
                v=t[(y0+int(py/scale))*512+x0+int(px/scale)]
                if v>TH:
                    X=int(x+(xo)*scale)+px;Y=int(base+yo*scale)+py
                    if 0<=X<W and 0<=Y<H:
                        p=(Y*W+X)*4; out[p:p+3]=bytes((239,230,210))
        x+=adv/256*scale
draw("Continue New Game Load Options Exit 12,480",20,60,1.0)
draw("Fateless One - Gorhart",20,120,1.0)
sheet.wr(sys.argv[5],W,H,out)
