#include "oa_audio.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
/* Compares this decoder with ffmpeg's output for a real sound of the game. Usage: oa_adpcm_test sound.bin reference.raw */
static uint8_t *load(const char *p,long *n){FILE *f=fopen(p,"rb");uint8_t *b;if(!f)exit(2);fseek(f,0,SEEK_END);*n=ftell(f);rewind(f);b=(uint8_t*)malloc((size_t)*n);if(fread(b,1,(size_t)*n,f)!=(size_t)*n)exit(2);fclose(f);return b;}
int main(int argc,char **argv){long sn,rn;uint8_t *s,*r;int ch,block,i;int16_t coefs[7][2];static int16_t pcm[8192];long at,total=0,diff=0,worst=0,base;const int16_t *ref;if(argc!=3)return 2;s=load(argv[1],&sn);r=load(argv[2],&rn);ref=(const int16_t*)r;
 ch=s[0x2e];block=s[0x38]|s[0x39]<<8;for(i=0;i<7;i++){coefs[i][0]=(int16_t)(s[0x42+i*4]|s[0x43+i*4]<<8);coefs[i][1]=(int16_t)(s[0x44+i*4]|s[0x45+i*4]<<8);}
 base=0x3e+(s[0x3c]|s[0x3d]<<8);
 for(at=base;at+block<=sn&&(total+1)*2<rn/ch;at+=block){int frames=oa_adpcm_block(s+at,block,ch,coefs,pcm,4096);for(i=0;i<frames*ch&&(total+1)*2<=rn;i++,total++){long d=labs((long)pcm[i]-(long)ref[total]);if(d)diff++;if(d>worst)worst=d;}}
 printf("adpcm samples %ld differing %ld worst %ld\n",total,diff,worst);return total<1000||worst>2;}
