import sys, zlib, struct
def rd(p):
    b=open(p,'rb').read(); i=8; idat=b''
    while i<len(b):
        n=struct.unpack('>I',b[i:i+4])[0]; t=b[i+4:i+8]; d=b[i+8:i+8+n]; i+=12+n
        if t==b'IHDR': w,h=struct.unpack('>II',d[:8])
        if t==b'IDAT': idat+=d
    r=zlib.decompress(idat); s=w*4+1
    return w,h,bytearray(b''.join(r[y*s+1:(y+1)*s] for y in range(h)))
def wr(p,w,h,x):
    c=lambda t,d: struct.pack('>I',len(d))+t+d+struct.pack('>I',zlib.crc32(t+d))
    rows=b''.join(b'\0'+bytes(x[y*w*4:(y+1)*w*4]) for y in range(h))
    open(p,'wb').write(b'\x89PNG\r\n\x1a\n'+c(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6,0,0,0))+c(b'IDAT',zlib.compress(rows,6))+c(b'IEND',b''))
def crop(src,x,y,cw,ch):
    w,h,d=src; o=bytearray()
    for r in range(y,y+ch): o+=d[(r*w+x)*4:(r*w+x+cw)*4]
    return cw,ch,o
