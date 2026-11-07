#include "amalur_blob.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned checks;
static void require(int condition,const char *message){if(!condition){fprintf(stderr,"FAIL: %s\n",message);exit(1);}checks++;}
static void put(unsigned char *b,uint32_t value){b[0]=(unsigned char)value;b[1]=(unsigned char)(value>>8);b[2]=(unsigned char)(value>>16);b[3]=(unsigned char)(value>>24);}
static void fixture(unsigned char b[48]){
    memset(b,0,48);put(b,32);put(b+4,8);put(b+8,24);put(b+12,40);put(b+24,0x3fc00000u);put(b+40,4);put(b+44,0);
}
static void rejected(unsigned char *b,size_t length,const amalur_blob_limits *limits,const char *fragment){
    char error[256];amalur_blob *blob=amalur_blob_parse(b,length,limits,error,sizeof(error));
    require(blob==NULL && strstr(error,fragment)!=NULL,fragment);amalur_blob_destroy(blob);
}
int main(void){
    unsigned char b[48],empty[8]={0};char error[256];amalur_blob *blob;uint32_t value,offset;float f;const unsigned char *span;amalur_blob_fixup entry;size_t length;amalur_blob_limits limit={0};
    fixture(b);blob=amalur_blob_parse(b,sizeof(b),NULL,error,sizeof(error));require(blob!=NULL,error);
    require(amalur_blob_fixup_count(blob)==2,"two fixup slots");
    require(amalur_blob_fixup_at(blob,0,&entry)&&entry.slot_offset==4&&entry.stored_file_offset==40&&entry.target_offset==32,"original order and file-to-payload offset retained");
    require(amalur_blob_fixup_at(blob,1,&entry)&&entry.slot_offset==0&&entry.stored_file_offset==24&&entry.target_offset==16,"second original entry and decoded offset retained");
    require(!amalur_blob_fixup_at(blob,2,&entry),"fixup index bounds");
    require(amalur_blob_resolve_span(blob,0,4,&span,&offset)&&offset==16&&span[2]==0xc0,"registered span resolves");
    require(!amalur_blob_resolve_span(blob,8,1,&span,NULL),"unregistered slots rejected");
    require(amalur_blob_resolve_span(blob,4,0,&span,&offset)&&offset==32,"zero span at one-past-end");
    require(!amalur_blob_resolve_span(blob,4,1,&span,NULL),"nonzero span at end rejected");
    require(!amalur_blob_resolve_span(blob,0,SIZE_MAX,&span,NULL),"span overflow rejected");
    require(amalur_blob_read_u32(blob,16,&value)&&value==0x3fc00000u,"little endian integer");
    require(amalur_blob_read_f32(blob,16,&f)&&f==1.5f,"float bits preserved");
    require(!amalur_blob_read_u32(blob,29,&value),"last incomplete word rejected");
    require(!amalur_blob_read_u32(blob,UINT32_MAX,&value),"integer offset overflow rejected");
    memset(b,0,sizeof(b));require(amalur_blob_read_u32(blob,0,&value)&&value==24,"stored file-relative word survives source mutation unchanged");
    require(amalur_blob_file_bytes(blob,&length)!=NULL&&length==48,"original file bytes retained");amalur_blob_destroy(blob);
    blob=amalur_blob_parse(empty,sizeof(empty),NULL,error,sizeof(error));require(blob!=NULL&&amalur_blob_fixup_count(blob)==0,"empty structural payload admitted");amalur_blob_destroy(blob);
    fixture(b);rejected(b,7,NULL,"truncated");
    rejected(b,47,NULL,"declared sections");
    limit.max_file_bytes=47;rejected(b,48,&limit,"byte limit");limit.max_file_bytes=0;
    limit.max_fixup_slots=1;rejected(b,48,&limit,"slot limit");limit.max_fixup_slots=0;
    put(b,33);put(b+4,7);rejected(b,48,NULL,"divisible");
    fixture(b);put(b,UINT32_MAX);put(b+4,UINT32_MAX);rejected(b,48,NULL,"declared sections");
    fixture(b);put(b+40,32);rejected(b,48,NULL,"slot exceeds");
    fixture(b);put(b+12,41);rejected(b,48,NULL,"target exceeds");
    fixture(b);put(b+12,UINT32_MAX);rejected(b,48,NULL,"target exceeds");
    fixture(b);put(b+40,0);rejected(b,48,NULL,"duplicate or overlapping");
    fixture(b);put(b+40,1);put(b+9,0);rejected(b,48,NULL,"duplicate or overlapping");
    fixture(b);put(b+8,0);rejected(b,48,NULL,"precedes payload");
    fixture(b);put(b+8,7);rejected(b,48,NULL,"precedes payload");
    fixture(b);put(b+8,8);blob=amalur_blob_parse(b,48,NULL,error,sizeof(error));require(blob!=NULL,error);
    require(amalur_blob_resolve_span(blob,0,4,&span,&offset)&&offset==0,"stored8 resolves to first payload byte without null semantics");amalur_blob_destroy(blob);
    require(amalur_blob_load_file("this-file-does-not-exist.opem",NULL,error,sizeof(error))==NULL&&strstr(error,"open")!=NULL,"missing file error");
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"structural container bounds and immutable relative offsets only\"}\n",checks);return 0;
}
