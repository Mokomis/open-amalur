#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdarg.h>
#include "oa_cosmetic_material.h"
#include "oa_cosmetic_texture_bank.h"
#include "oa_appearance_selection.h"
#define ROOT "C:/Users/rwill/Documents/Opem Amalur/"
#define AS ROOT "work/v50-character-complete/appearance-assets/"
#define ENV ROOT "work/v50-character-complete/environment-vetting/"
int __android_log_print(int l,const char*t,const char*f,...){va_list a;int n;(void)l;fprintf(stderr,"%s: ",t);va_start(a,f);n=vfprintf(stderr,f,a);va_end(a);fputc('\n',stderr);return n;}
void oa_desktop_material_probe_texture(GLuint x,int w,int h,const char*s){(void)x;(void)w;(void)h;(void)s;}
static void fail(const char*s){fprintf(stderr,"FAIL %s GL%x EGL%x\n",s,glGetError(),eglGetError());exit(2);}
static int readfile(void*user,const char*path,uint8_t**b,size_t*n){FILE*f;long z;(void)user;*b=NULL;*n=0;f=fopen(path,"rb");if(!f)return 0;fseek(f,0,SEEK_END);z=ftell(f);rewind(f);if(z<=0){fclose(f);return 0;}*b=malloc(z);if(!*b||fread(*b,1,z,f)!=(size_t)z){free(*b);*b=NULL;fclose(f);return 0;}fclose(f);*n=z;return 1;}
typedef struct {uint8_t*b;oa_am_model m;} cache_row;
static cache_row cache[64];static unsigned cached;
static int model(void*u,uint32_t fab,oa_am_model*out){unsigned i;char path[768];size_t n;(void)u;for(i=0;i<cached;i++)if(cache[i].m.fab==fab){*out=cache[i].m;return 1;}if(cached>=64)return 0;snprintf(path,sizeof(path),AS"models/%u.oaam",fab);if(!readfile(NULL,path,&cache[cached].b,&n)||!oa_am_open(&cache[cached].m,cache[cached].b,n))return 0;*out=cache[cached++].m;return 1;}
static GLuint cube(const char*path){uint8_t*b;size_t n;GLuint t;unsigned i;if(!readfile(NULL,path,&b,&n)||n!=1536)fail("sourcecube");glGenTextures(1,&t);glBindTexture(GL_TEXTURE_CUBE_MAP,t);for(i=0;i<6;i++)glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+i,0,GL_RGBA8,8,8,0,GL_RGBA,GL_UNSIGNED_BYTE,b+i*256);free(b);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAX_LEVEL,0);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);return t;}
int main(int argc,char**argv){EGLDisplay d;EGLConfig cfg;EGLContext ec;EGLSurface es;EGLint n,ma,mi;GLuint cc,wc,ubo;float zero[113*8]={0},worlds[32*64*12],pal[78*12],entity[12]={1,0,0,0,0,1,0,0,0,0,1,0};oa_cm_texture_bank bank={0};oa_cm_context cm={0};oa_ap_selection selection={0};oa_ap_plan plan;oa_creation_state st;oa_creation_render_selection render;oa_cm_instance inst;uint8_t*clip,*pixels;size_t cn;uint32_t rootbones,c,a,pass;unsigned draws=0,triangles=0,opaque=0,transparent=0;FILE*log;
 const EGLint ca[]={EGL_SURFACE_TYPE,EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES3_BIT_KHR,EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_DEPTH_SIZE,24,EGL_NONE},sa[]={EGL_WIDTH,512,EGL_HEIGHT,512,EGL_NONE},xa[]={EGL_CONTEXT_CLIENT_VERSION,3,EGL_NONE};
 float vp[16]={1.f/125,0,0,0,0,0,1.f/400,0,0,1.f/125,0,0,0,-90.f/125,0,1},eye[3]={0,-400,90};
 if(!oa_ap_plan_build(&selection,model,NULL,&plan))fail("sourceplan");if(!readfile(NULL,AS"clips/1507280-703318.local-trs.bin",&clip,&cn)||cn<12)fail("actualsourceclip");memcpy(&rootbones,clip,4);if(rootbones!=64||!oa_ap_plan_pose(&plan,model,NULL,(const float*)(clip+12),rootbones,worlds,sizeof(worlds)/4))fail("actualsourcepose");
 if(oa_creation_begin(&st,0,0)!=OA_CREATION_OK||oa_creation_render(&st,&render)!=OA_CREATION_OK||!oa_cm_instance_from_selection(&render,255,&inst))fail("sourcecreationselection");if(inst.tattoo_texture!=plan.tattoo_texture)fail("tattooselectionjoin");
 d=eglGetDisplay(EGL_DEFAULT_DISPLAY);if(!eglInitialize(d,&ma,&mi)||!eglBindAPI(EGL_OPENGL_ES_API)||!eglChooseConfig(d,ca,&cfg,1,&n)||!n)fail("EGL");es=eglCreatePbufferSurface(d,cfg,sa);ec=eglCreateContext(d,cfg,EGL_NO_CONTEXT,xa);if(!eglMakeCurrent(d,es,es,ec))fail("context");cc=cube(ENV"1583578-env0-character-cube1.rgba");wc=cube(ENV"1583578-env0-world-cube0.rgba");
 if(!oa_cm_bank_open(&bank,readfile,NULL,"textures/")||!oa_cm_open(&cm,cc,wc,oa_cm_bank_texture,&bank,113))fail("resourcesopen");
 glGenBuffers(1,&ubo);glBindBuffer(GL_UNIFORM_BUFFER,ubo);glBufferData(GL_UNIFORM_BUFFER,sizeof(zero),zero,GL_STATIC_DRAW);glBindBufferBase(GL_UNIFORM_BUFFER,0,ubo);glViewport(0,0,512,512);glClearColor(0,0,0,0);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LEQUAL);if(argc>1&&atoi(argv[1])){glEnable(GL_CULL_FACE);glCullFace(GL_BACK);glFrontFace(atoi(argv[1])==1?GL_CW:GL_CCW);}else glDisable(GL_CULL_FACE);
 log=fopen("cull-surfaces.csv","w");fprintf(log,"component,fab,assembly,material,kind,vertices,indices,palette,pass\n");
 for(pass=0;pass<2;pass++){if(pass){glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);glDepthMask(GL_FALSE);}else{glDisable(GL_BLEND);glDepthMask(GL_TRUE);}
  for(c=0;c<plan.count;c++){oa_am_model mod;oa_am_chunk bones;if(!model(NULL,plan.component[c].fab,&mod)||!oa_am_find(&mod,"BONE",&bones))fail("modelchunk");
   for(a=0;a<oa_am_surface_count(&mod);a++){oa_am_surface sf;oa_cm_surface gpu={0};oa_cm_material mat;oa_cm_vertex*v;unsigned i;int beard;const oa_ap_option*option;
    if(!oa_am_surface_get(&mod,a,&sf))fail("surfaceparse");if(!oa_ap_component_surface_visible(&plan,c,&sf)||!sf.index_count)continue;if(!oa_cm_material_find(sf.material_id,&mat))fail("materialmissing");if((mat.kind==OA_CM_FOG_ADDITIVE)!=(pass!=0))continue;
    v=malloc((size_t)sf.vertex_count*96);memcpy(v,sf.vertices96,(size_t)sf.vertex_count*96);for(i=0;i<sf.vertex_count;i++)if(!(v[i].flags&OA_CM_HAS_COLOR)){memset(v[i].rgba,255,4);v[i].flags|=OA_CM_NATIVE_DEFAULT_COLOR;}
    {unsigned pos=0,neg=0,k;for(k=0;k+2<sf.index_count;k+=3){oa_cm_vertex *a0=v+sf.indices[k],*b0=v+sf.indices[k+1],*c0=v+sf.indices[k+2];float e[3],f[3],cross[3],nn[3],dt;unsigned j;for(j=0;j<3;j++){e[j]=b0->p[j]-a0->p[j];f[j]=c0->p[j]-a0->p[j];nn[j]=a0->n[j]+b0->n[j]+c0->n[j];}cross[0]=e[1]*f[2]-e[2]*f[1];cross[1]=e[2]*f[0]-e[0]*f[2];cross[2]=e[0]*f[1]-e[1]*f[0];dt=cross[0]*nn[0]+cross[1]*nn[1]+cross[2]*nn[2];if(dt>1e-6)pos++;else if(dt< -1e-6)neg++;}printf("winding fab%u asm%u dotNormal pos%u neg%u\n",mod.fab,a,pos,neg);}
    if(!oa_cm_surface_open(&gpu,v,sf.vertex_count,sf.indices,sf.index_count,sf.palette_count,sf.weighted))fail("actualsurfaceupload");free(v);
    if(!oa_am_palette(&mod,a,worlds+c*64*12,bones.count,NULL,pal,sizeof(pal)/4))fail("sourcepalette");
    if(!oa_cm_resources_ready(&cm,&mat,&inst))fail("reservation");if(!oa_cm_begin(&cm,eye))fail("begin");option=oa_ap_option_get(plan.component[c].source_type);beard=option&&option->category_hash==0x11651bu;
    if(oa_cm_draw(&cm,&gpu,&mat,&inst,beard,vp,pal,entity)!=1)fail("actualdraw");fprintf(log,"%u,%u,%u,%u,%u,%u,%u,%u,%u\n",c,mod.fab,a,mat.material,mat.kind,sf.vertex_count,sf.index_count,sf.palette_count,pass);draws++;triangles+=sf.index_count/3;if(pass)transparent++;else opaque++;oa_cm_surface_close(&gpu);
   }
  }
 }
 fclose(log);pixels=malloc(512*512*4);glReadPixels(0,0,512,512,GL_RGBA,GL_UNSIGNED_BYTE,pixels);log=fopen("cull-result.rgba","wb");fwrite(pixels,1,512*512*4,log);fclose(log);{unsigned nonzero=0,i;for(i=0;i<512*512;i++)if(pixels[4*i+3])nonzero++;if(nonzero<1000)fail("emptyactualappearance");printf("PASSactualsourceAlmainMale frame0 draws%u opaque%u transparent%u triangles%u pixels%u textures%u\n",draws,opaque,transparent,triangles,nonzero,bank.count);}free(pixels);oa_cm_close(&cm);oa_cm_bank_close(&bank);return 0;}
