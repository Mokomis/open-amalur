"""Bounded observed KEEN texture carrier + standard BC1/BC3 decoder.
Carrier fields are a selected-sample hypothesis until native-loader evidence
is attached; a .dds extension is not treated as a standard DDS container.
BC reference: Microsoft Direct3D block-compression documentation.
"""
import argparse,hashlib,json,platform,struct,zlib
from pathlib import Path
BC_REFERENCE='https://learn.microsoft.com/en-us/windows/win32/direct3d10/d3d10-graphics-programming-guide-resources-block-compression'
MAX_DIMENSION=4096;MAX_FILE_BYTES=32*1024*1024

def rgb565(v):
    r=(v>>11)&31;g=(v>>5)&63;b=v&31
    return ((r<<3)|(r>>2),(g<<2)|(g>>4),(b<<3)|(b>>2))
def color_block(block,force_four=False):
    c0,c1,bits=struct.unpack('<HHI',block);a=rgb565(c0);b=rgb565(c1)
    colors=[(*a,255),(*b,255)]
    if c0>c1 or force_four:
        colors.extend([(*( (2*a[i]+b[i])//3 for i in range(3)),255),(*( (a[i]+2*b[i])//3 for i in range(3)),255)])
    else:colors.extend([(*( (a[i]+b[i])//2 for i in range(3)),255),(0,0,0,0)])
    return [colors[(bits>>(2*i))&3] for i in range(16)]
def bc3_block(block):
    a,b=block[:2];bits=int.from_bytes(block[2:8],'little');alphas=[a,b]
    if a>b:alphas.extend(((7-i)*a+i*b)//7 for i in range(1,7))
    else:alphas.extend(((5-i)*a+i*b)//5 for i in range(1,5));alphas.extend([0,255])
    colors=color_block(block[8:],True)
    return [(*colors[i][:3],alphas[(bits>>(3*i))&7]) for i in range(16)]
def decode_blocks(data,width,height,fmt):
    if fmt not in (1,5) or not 1<=width<=MAX_DIMENSION or not 1<=height<=MAX_DIMENSION:raise ValueError('Unsupported bounded BC shape')
    size=8 if fmt==1 else 16;bx=(width+3)//4;by=(height+3)//4
    if len(data)!=bx*by*size:raise ValueError('Exact BC block payload required')
    output=bytearray(width*height*4)
    for y in range(by):
        for x in range(bx):
            at=(y*bx+x)*size;block=data[at:at+size];colors=color_block(block) if fmt==1 else bc3_block(block)
            for row in range(4):
                if y*4+row>=height:continue
                for col in range(4):
                    if x*4+col>=width:continue
                    p=((y*4+row)*width+x*4+col)*4;output[p:p+4]=bytes(colors[row*4+col])
    return bytes(output)
def parse(data):
    if not 38<=len(data)<=MAX_FILE_BYTES or data[16:20]!=b'KEEN':raise ValueError('Observed KEEN carrier required')
    asset=struct.unpack_from('<I',data,0)[0];original_w,original_h=struct.unpack_from('<HH',data,4)
    shift,unknown=struct.unpack_from('<II',data,8);w,h=struct.unpack_from('<HH',data,20)
    fmt=data[29];mips=struct.unpack_from('<H',data,35)[0]
    if unknown or data[24:29]!=b'\x01\x00\x01\x00\x01' or data[30:35]!=b'\0'*5 or data[37]!=1:raise ValueError('Unadmitted KEEN header fields')
    for d in (w,h,original_w,original_h):
        if not 4<=d<=MAX_DIMENSION or d&(d-1):raise ValueError('Selected KEEN profile requires power-of-two dimensions4..4096')
    if shift>10 or original_w>>shift!=w or original_h>>shift!=h:raise ValueError('KEEN stored dimensions disagree with selected mip shift')
    if fmt not in (1,5):raise ValueError('Selected KEEN profile supports only observed format1/5')
    levels=[];at=38;lw,lh=w,h;block=8 if fmt==1 else 16
    while True:
        size=((lw+3)//4)*((lh+3)//4)*block
        if size>len(data)-at:raise ValueError('Truncated KEEN mip payload')
        levels.append({'level':len(levels),'width':lw,'height':lh,'offset':at,'bytes':size});at+=size
        if lw<=4 and lh<=4:break
        lw=max(1,lw//2);lh=max(1,lh//2)
    if len(levels)!=mips or at!=len(data):raise ValueError('KEEN mip count or exact consumption mismatch')
    return {'asset_id':asset,'original_width':original_w,'original_height':original_h,'selected_mip_shift':shift,
        'width':w,'height':h,'observed_format':fmt,'bc_format':'BC1' if fmt==1 else 'BC3','mips':levels,
        'source_bytes':len(data),'source_sha256':hashlib.sha256(data).hexdigest(),'header_hex':data[:38].hex(),
        'carrier_scope':'Observed strict selected-sample KEEN header/mip layout; native-loader confirmation pending.',
        'bc_reference':BC_REFERENCE,'pixel_policy':'Unmodified stored UV/row convention; no vertical flip. RGB565 bit expansion and integer-floor interpolation into RGBA8; no native GPU rounding/color-space parity claim.'}
def decode(data,level=0):
    info=parse(data)
    if type(level)is not int or not 0<=level<len(info['mips']):raise ValueError('Requested existing mip is absent')
    mip=info['mips'][level];rgba=decode_blocks(data[mip['offset']:mip['offset']+mip['bytes']],mip['width'],mip['height'],info['observed_format'])
    info.update(decoded_level=level,decoded_width=mip['width'],decoded_height=mip['height'],rgba_bytes=len(rgba),rgba_sha256=hashlib.sha256(rgba).hexdigest(),alpha_min=min(rgba[3::4]),alpha_max=max(rgba[3::4]))
    return rgba,info

def write_png(path,width,height,rgba):
    if len(rgba)!=width*height*4:raise ValueError('Exact RGBA buffer required for PNG')
    def chunk(kind,payload):
        return struct.pack('>I',len(payload))+kind+payload+struct.pack('>I',zlib.crc32(kind+payload)&0xffffffff)
    rows=b''.join(b'\0'+rgba[y*width*4:(y+1)*width*4] for y in range(height))
    png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',width,height,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')
    Path(path).write_bytes(png)

def main():
    assert platform.system()=='Windows','fresh artifact decoding runs on Windows'
    ap=argparse.ArgumentParser();ap.add_argument('input',type=Path);ap.add_argument('--rgba',required=True,type=Path);ap.add_argument('--report',required=True,type=Path)
    ap.add_argument('--png',type=Path);ap.add_argument('--level',type=int,default=0);args=ap.parse_args()
    if args.input.stat().st_size>MAX_FILE_BYTES:raise ValueError('Input byte bound exceeded')
    rgba,info=decode(args.input.read_bytes(),args.level)
    args.rgba.parent.mkdir(parents=True,exist_ok=True);args.rgba.write_bytes(rgba);info['input_file']=str(args.input);info['rgba_file']=str(args.rgba)
    if args.png:
        args.png.parent.mkdir(parents=True,exist_ok=True);write_png(args.png,info['decoded_width'],info['decoded_height'],rgba);info['png_file']=str(args.png)
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(info,indent=2),encoding='utf-8');print(json.dumps(info,indent=2))
if __name__=='__main__':main()
