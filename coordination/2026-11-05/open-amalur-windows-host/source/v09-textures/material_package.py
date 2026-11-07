"""Author OMAT09 sidecars from explicitly verified UV/draw/RGBA inputs.
No native material, texture slot, archive precedence or UV layout is inferred.
"""
import hashlib,math,struct
MAGIC=b'OMAT09\0\0';MAX_BYTES=384*1024*1024;FALLBACK=0xffffffff
MAX_VERTICES=8000000;MAX_DRAWS=4096;MAX_TEXTURES=256;MAX_DIMENSION=4096

def encode(scene,uvs,draws,textures):
    if len(scene)<36 or scene[:8]!=b'OMSC07\0\0':raise ValueError('Verified OMSC07 geometry required')
    count=struct.unpack_from('<I',scene,8)[0]
    if not count or count>MAX_VERTICES or count%3 or len(scene)!=36+count*36:raise ValueError('Scene shape invalid')
    if len(uvs)!=count or not 1<=len(draws)<=MAX_DRAWS or len(textures)>MAX_TEXTURES:raise ValueError('Sidecar counts invalid')
    data=bytearray(MAGIC+struct.pack('<4I',1,count,len(draws),len(textures))+hashlib.sha256(scene).digest())
    for uv in uvs:
        if len(uv)!=2 or any(not isinstance(v,(int,float)) or not math.isfinite(v) for v in uv):raise ValueError('Finite unmodified UV pairs required')
        packed=struct.pack('<2f',*uv)
        if not all(math.isfinite(v) for v in struct.unpack('<2f',packed)):raise ValueError('UV exceeds float32 domain')
        data+=packed
    next_vertex=0
    for draw in draws:
        first,count_draw,texture=draw['first_vertex'],draw['vertex_count'],draw['texture_index']
        if any(type(v)is not int for v in [first,count_draw,texture]):raise ValueError('Integer draw fields required')
        if first!=next_vertex or count_draw<=0 or count_draw%3 or count_draw>count-next_vertex or (texture!=FALLBACK and not 0<=texture<len(textures)):raise ValueError('Full contiguous triangle coverage and valid texture references required')
        data+=struct.pack('<4I',first,count_draw,texture,0);next_vertex+=count_draw
    if next_vertex!=count:raise ValueError('Incomplete draw coverage')
    gpu_bytes=count*8
    for texture in textures:
        w,h,rgba=texture['width'],texture['height'],texture['rgba']
        if type(w)is not int or type(h)is not int or not 1<=w<=MAX_DIMENSION or not 1<=h<=MAX_DIMENSION or len(rgba)!=w*h*4:raise ValueError('Bounded exact RGBA8 texture required')
        if len(data)+16+len(rgba)>MAX_BYTES:raise ValueError('Package exceeds byte bound')
        data+=struct.pack('<4I',w,h,len(rgba),0)+rgba
        while True:
            gpu_bytes+=w*h*4
            if gpu_bytes>MAX_BYTES:raise ValueError('GLES mip-chain plus UV budget exceeded')
            if w==1 and h==1:break
            w=max(1,w//2);h=max(1,h//2)
    if len(data)>MAX_BYTES:raise ValueError('Package exceeds byte bound')
    return bytes(data),{'format':'OMAT09 authored sidecar version1','scene_sha256':hashlib.sha256(scene).hexdigest(),
        'vertices':count,'draws':len(draws),'textures':len(textures),'package_bytes':len(data),
        'package_sha256':hashlib.sha256(data).hexdigest(),'gpu_bytes_including_generated_mips':gpu_bytes,
        'textured_vertices':sum(d['vertex_count'] for d in draws if d['texture_index']!=FALLBACK),
        'fallback_vertices':sum(d['vertex_count'] for d in draws if d['texture_index']==FALLBACK)}
