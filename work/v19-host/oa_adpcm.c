#include "oa_audio.h"
static int clamp16(int v){return v<-32768?-32768:v>32767?32767:v;}
int oa_adpcm_block(const uint8_t *b,int size,int ch,const int16_t coefs[][2],int16_t *out,int max_frames){
 static const int adapt[16]={230,230,230,230,307,409,512,614,768,614,512,409,307,230,230,230};
 int pred[2],delta[2],s1[2],s2[2],c,head=7*ch,frames=0,nib;
 if(size<head||max_frames<2)return 0;
 for(c=0;c<ch;c++){pred[c]=b[c];if(pred[c]>6)pred[c]=0;}
 for(c=0;c<ch;c++)delta[c]=(int16_t)(b[ch+c*2]|b[ch+c*2+1]<<8);
 for(c=0;c<ch;c++)s1[c]=(int16_t)(b[3*ch+c*2]|b[3*ch+c*2+1]<<8);
 for(c=0;c<ch;c++)s2[c]=(int16_t)(b[5*ch+c*2]|b[5*ch+c*2+1]<<8);
 for(c=0;c<ch;c++)out[c]=(int16_t)s2[c];
 for(c=0;c<ch;c++)out[ch+c]=(int16_t)s1[c];
 frames=2;c=0;
 for(nib=0;nib<(size-head)*2&&frames<max_frames;nib++){
  int byte=b[head+nib/2],code=nib&1?byte&15:byte>>4,sign=code>=8?code-16:code,p;
  p=(s1[c]*coefs[pred[c]][0]+s2[c]*coefs[pred[c]][1])/256+sign*delta[c];p=clamp16(p);
  s2[c]=s1[c];s1[c]=p;delta[c]=delta[c]*adapt[code]/256;if(delta[c]<16)delta[c]=16;
  out[frames*ch+c]=(int16_t)p;
  if(++c==ch){c=0;frames++;}}
 return frames;
}
