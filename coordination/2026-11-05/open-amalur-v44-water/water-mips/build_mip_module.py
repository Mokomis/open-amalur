from pathlib import Path
import hashlib,json
Q=Path(__file__).resolve().parent;R=Q.parent;p=R/'oa_native_water.c';old=p.read_text();s=old
s=s.replace('typedef struct {unsigned id,faces,w,h;const unsigned char *pixels;GLuint gpu;} tex;', 'typedef struct {unsigned w,h,bytes;const unsigned char *pixels;} mip;\ntypedef struct {unsigned id,faces,w,h,levels;mip level[16];GLuint gpu;} tex;')
s=s.replace('u32(p+4)!=1','u32(p+4)!=2')
a=s.index(' for(i=0;i<s->nt;i++){tex*t=s->t+i;unsigned bytes;');b=s.index('\n for(i=0;i<s->nm;i++){mesh*m=s->m+i;if(!take',a)
s=s[:a]+''' for(i=0;i<s->nt;i++){tex*t=s->t+i;unsigned total,seen=0,k;if(!take(s,&o,24,&p))goto bad;t->id=u32(p);t->faces=u32(p+4);t->w=u32(p+8);t->h=u32(p+12);t->levels=u32(p+16);total=u32(p+20);if((t->faces!=1&&t->faces!=6)||!t->w||!t->h||t->w>8192||t->h>8192||!t->levels||t->levels>16)goto bad;
  for(k=0;k<t->levels;k++){mip*l=t->level+k;unsigned expectedw=t->w>>k,expectedh=t->h>>k;if(!expectedw)expectedw=1;if(!expectedh)expectedh=1;if(!take(s,&o,12,&p))goto bad;l->w=u32(p);l->h=u32(p+4);l->bytes=u32(p+8);if(l->w!=expectedw||l->h!=expectedh||l->bytes!=(size_t)l->w*l->h*t->faces*4||!take(s,&o,l->bytes,&p))goto bad;l->pixels=p;if(seen>UINT32_MAX-l->bytes)goto bad;seen+=l->bytes;}if(seen!=total)goto bad;}
''' +s[b:]
a=s.index(' for(i=0;i<s->nt;i++){tex*t=s->t+i;GLenum target=');b=s.index('\n for(i=0;i<s->nm;i++){mesh*m=s->m+i;const unsigned sizes',a)
s=s[:a]+''' for(i=0;i<s->nt;i++){tex*t=s->t+i;unsigned k;GLenum target=t->faces==6?GL_TEXTURE_CUBE_MAP:GL_TEXTURE_2D;glGenTextures(1,&t->gpu);glBindTexture(target,t->gpu);for(k=0;k<t->levels;k++){mip*l=t->level+k;for(j=0;j<t->faces;j++)glTexImage2D(t->faces==6?GL_TEXTURE_CUBE_MAP_POSITIVE_X+j:GL_TEXTURE_2D,k,GL_RGBA8,l->w,l->h,0,GL_RGBA,GL_UNSIGNED_BYTE,l->pixels+(size_t)j*l->w*l->h*4);}glTexParameteri(target,GL_TEXTURE_BASE_LEVEL,0);glTexParameteri(target,GL_TEXTURE_MAX_LEVEL,t->levels-1);glTexParameteri(target,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);glTexParameteri(target,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(target,GL_TEXTURE_WRAP_S,t->faces==6?GL_CLAMP_TO_EDGE:GL_REPEAT);glTexParameteri(target,GL_TEXTURE_WRAP_T,t->faces==6?GL_CLAMP_TO_EDGE:GL_REPEAT);if(t->faces==6)glTexParameteri(target,GL_TEXTURE_WRAP_R,GL_CLAMP_TO_EDGE);}
''' +s[b:]
assert s!=old and 'glGenerateMipmap' not in s and 't->pixels' not in s
out=R/'oa_native_water_mips.c';out.write_text(s);names=['water_vs','water_fs'];shader_hashes={}
for name in names:
 start=old.index('static const char '+name+'[]');end=old.index(';\n',start)+2;assert old[start:end] in s;shader_hashes[name]=hashlib.sha256(old[start:end].encode()).hexdigest()
(Q/'water-mip-source-validation.json').write_text(json.dumps(dict(source_v1_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_v2_sha256=hashlib.sha256(out.read_bytes()).hexdigest(),shader_source_literals_identical=True,shader_source_hashes=shader_hashes,header_unchanged_sha256=hashlib.sha256((R/'oa_native_water.h').read_bytes()).hexdigest(),no_generate_mipmap=True,max_level_matches_recorded_chain=True),indent=2));print('New loader generated; shaders/header unchanged; no mipgeneration')
