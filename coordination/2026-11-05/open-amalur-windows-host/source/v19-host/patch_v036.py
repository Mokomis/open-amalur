from pathlib import Path
R=Path.home()/"Documents/Opem Amalur";r=R/"work/v19-host"
def edit(f,fn):
    s=f.read_bytes().decode();crlf="\r\n" in s;s=s.replace("\r\n","\n");s=fn(s)
    if crlf:s=s.replace("\n","\r\n")
    f.write_bytes(s.encode())
def rep(s,a,b):
    assert a in s,a[:70]
    return s.replace(a,b,1)
def scene(s):
    s=rep(s,"world_programs[5];","world_programs[4];")
    s=rep(s,"{int wi;for(wi=0;wi<5;wi++)if(g->world_programs[wi])","{int wi;for(wi=0;wi<4;wi++)if(g->world_programs[wi])")
    s=rep(s,"{int wi,all=1;for(wi=0;wi<5;wi++){g->world_programs[wi]=","{int wi,all=1;for(wi=0;wi<4;wi++){g->world_programs[wi]=")
    s=rep(s,"for(v=0;v<5;v++){GLuint w=g->world_programs[v];","for(v=0;v<4;v++){GLuint w=g->world_programs[v];")
    s=rep(s,'/* The fog value is real; its scale is authored, since the mapping into the game\'s fog constants is not recovered. */glUniform2f(glGetUniformLocation(w,"fog"),0.f,oa_live_fog_density*1.2e-7f);','/* The game\'s fog constants. */glUniform2f(glGetUniformLocation(w,"fog"),oa_live_fog_density/500000.f,oa_live_fog_start);')
    return s
edit(r/"android_scene.c",scene)
def bc(s):
    s=rep(s,'HEADS = [1362163]','HEADS = ["1362163"]')
    s=rep(s,'print("head candidate", syms["fab"][hid], hid,','print("head candidate", syms["fab"].get(hid), hid,')
    return s
edit(R/"work/v20-char/build_character.py",bc)
print("ok")
