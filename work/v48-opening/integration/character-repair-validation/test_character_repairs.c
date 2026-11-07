#include "oa_character_attributes.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
#define CHECK(x) do{checks++;if(!(x)){fprintf(stderr,"FAIL line%d: %s\n",__LINE__,#x);return 1;}}while(0)
static unsigned char *readall(const char *p,size_t *n){FILE *f=fopen(p,"rb");long len;unsigned char *b;if(!f)return NULL;fseek(f,0,SEEK_END);len=ftell(f);rewind(f);if(len<0){fclose(f);return NULL;}*n=(size_t)len;b=malloc(*n+1);if(!b||fread(b,1,*n,f)!=*n){free(b);fclose(f);return NULL;}fclose(f);return b;}
int main(int argc,char **argv){
 unsigned char *original,*work,*attrs,*pal;size_t n=0,an=0,pn=0;unsigned normals=0,parts=0;char error[256];FILE *out;
 CHECK(argc==5);original=readall(argv[1],&n);attrs=readall(argv[2],&an);pal=readall(argv[3],&pn);CHECK(original&&attrs&&pal);
 work=malloc(n);CHECK(work);memcpy(work,original,n);
 CHECK(oa_character_repairs_apply(work,n,attrs,an,pal,pn,&normals,&parts,error,sizeof(error)));CHECK(normals==2781&&parts==2);CHECK(memcmp(work,original,n)!=0);
 out=fopen(argv[4],"wb");CHECK(out);CHECK(fwrite(work,1,n,out)==n);CHECK(fclose(out)==0);
 memcpy(work,original,n);pal[700]^=1;
 CHECK(!oa_character_repairs_apply(work,n,attrs,an,pal,pn,&normals,&parts,error,sizeof(error)));CHECK(normals==0&&parts==0&&!memcmp(work,original,n));pal[700]^=1;
 attrs[700]^=1;
 CHECK(!oa_character_repairs_apply(work,n,attrs,an,pal,pn,&normals,&parts,error,sizeof(error)));CHECK(normals==0&&parts==0&&!memcmp(work,original,n));attrs[700]^=1;
 CHECK(!oa_character_repairs_apply(work,n,attrs,an-1,pal,pn,&normals,&parts,error,sizeof(error)));CHECK(!memcmp(work,original,n));
 CHECK(!oa_character_repairs_apply(work,n,attrs,an,pal,pn-1,&normals,&parts,error,sizeof(error)));CHECK(!memcmp(work,original,n));
 work[n/2]^=1;original[n/2]^=1;
 CHECK(!oa_character_repairs_apply(work,n,attrs,an,pal,pn,&normals,&parts,error,sizeof(error)));CHECK(!memcmp(work,original,n));
 work[n/2]^=1;original[n/2]^=1;
 CHECK(!oa_character_repairs_apply(work,0,attrs,an,pal,pn,&normals,&parts,error,sizeof(error)));CHECK(!memcmp(work,original,n));
 CHECK(oa_character_repairs_apply(work,n,attrs,an,pal,pn,NULL,NULL,error,sizeof(error)));
 printf("{\"checks\":%u,\"normal_defects_corrected\":2781,\"palette_parts\":2,\"failure_atomic\":true}\n",checks);
 free(original);free(work);free(attrs);free(pal);return 0;
}
