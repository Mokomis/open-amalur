#include "amalur_blob.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>

struct amalur_blob {
    unsigned char *file;
    size_t file_size;
    uint32_t payload_size, slot_count;
    uint32_t *sorted_slots;
};
static void diagnostic(char *error,size_t cap,const char *message) {
    size_t n;
    if(!error || !cap)return;
    n=strlen(message);if(n>=cap)n=cap-1;
    memcpy(error,message,n);error[n]=0;
}
static uint32_t little_u32(const unsigned char *p) {
    return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);
}
static size_t file_limit(const amalur_blob_limits *limits) {
    return limits && limits->max_file_bytes ? limits->max_file_bytes : 64u*1024u*1024u;
}
static int compare_u32(const void *a,const void *b) {
    uint32_t x=*(const uint32_t*)a,y=*(const uint32_t*)b;
    return x<y?-1:x>y?1:0;
}
static int registered(const amalur_blob *b,uint32_t slot) {
    uint32_t lo=0,hi=b->slot_count;
    while(lo<hi){uint32_t mid=lo+(hi-lo)/2;uint32_t value=b->sorted_slots[mid];
        if(value==slot)return 1;if(value<slot)lo=mid+1;else hi=mid;}
    return 0;
}
amalur_blob *amalur_blob_parse(const void *bytes,size_t length,const amalur_blob_limits *limits,char *error,size_t cap) {
    const unsigned char *source=(const unsigned char*)bytes;
    uint32_t payload,fixup_bytes,slots,i,maximum_slots;
    uint64_t total;
    amalur_blob *b=NULL;
    diagnostic(error,cap,"");
    if(!source || length<8){diagnostic(error,cap,"truncated container header");return NULL;}
    if(length>file_limit(limits)){diagnostic(error,cap,"container exceeds configured byte limit");return NULL;}
    payload=little_u32(source);fixup_bytes=little_u32(source+4);
    total=8u+(uint64_t)payload+(uint64_t)fixup_bytes;
    if(total!=(uint64_t)length){diagnostic(error,cap,"container size does not match declared sections");return NULL;}
    if(fixup_bytes%4){diagnostic(error,cap,"fixup table byte count is not divisible by four");return NULL;}
    slots=fixup_bytes/4;
    maximum_slots=limits && limits->max_fixup_slots ? limits->max_fixup_slots : 1048576u;
    if(slots>maximum_slots){diagnostic(error,cap,"fixup table exceeds configured slot limit");return NULL;}
    if((uint64_t)slots*sizeof(uint32_t)>(uint64_t)SIZE_MAX){diagnostic(error,cap,"fixup allocation size overflows host");return NULL;}
    b=(amalur_blob*)calloc(1,sizeof(*b));
    if(!b){diagnostic(error,cap,"container allocation failed");return NULL;}
    b->file=(unsigned char*)malloc(length);
    if(!b->file){diagnostic(error,cap,"container byte allocation failed");goto fail;}
    memcpy(b->file,source,length);b->file_size=length;b->payload_size=payload;b->slot_count=slots;
    if(slots){
        b->sorted_slots=(uint32_t*)malloc((size_t)slots*sizeof(uint32_t));
        if(!b->sorted_slots){diagnostic(error,cap,"fixup index allocation failed");goto fail;}
    }
    for(i=0;i<slots;i++){
        uint32_t slot=little_u32(b->file+8+(size_t)payload+(size_t)i*4);
        if(payload<4 || slot>payload-4){diagnostic(error,cap,"fixup slot exceeds payload bounds");goto fail;}
        b->sorted_slots[i]=slot;
    }
    if(slots)qsort(b->sorted_slots,slots,sizeof(uint32_t),compare_u32);
    for(i=1;i<slots;i++){
        if(b->sorted_slots[i]-b->sorted_slots[i-1]<4){diagnostic(error,cap,"duplicate or overlapping fixup slots");goto fail;}
    }
    for(i=0;i<slots;i++){
        uint32_t stored=little_u32(b->file+8+b->sorted_slots[i]);
        if(stored<8){diagnostic(error,cap,"fixup stored file offset precedes payload");goto fail;}
        if(stored-8>payload){diagnostic(error,cap,"fixup target exceeds payload bounds");goto fail;}
    }
    return b;
fail:
    amalur_blob_destroy(b);return NULL;
}
amalur_blob *amalur_blob_load_file(const char *path,const amalur_blob_limits *limits,char *error,size_t cap) {
    FILE *file;long end;size_t length;unsigned char *bytes;amalur_blob *result;
    diagnostic(error,cap,"");
    if(!path){diagnostic(error,cap,"container path is required");return NULL;}
    file=fopen(path,"rb");if(!file){diagnostic(error,cap,"cannot open container file");return NULL;}
    if(fseek(file,0,SEEK_END) || (end=ftell(file))<0 || fseek(file,0,SEEK_SET)){
        diagnostic(error,cap,"cannot determine container file length");fclose(file);return NULL;}
    if((uint64_t)end>(uint64_t)file_limit(limits) || (uint64_t)end>(uint64_t)SIZE_MAX){
        diagnostic(error,cap,"container exceeds configured byte limit");fclose(file);return NULL;}
    length=(size_t)end;
    if(length<8){diagnostic(error,cap,"truncated container header");fclose(file);return NULL;}
    bytes=(unsigned char*)malloc(length);
    if(!bytes){diagnostic(error,cap,"file buffer allocation failed");fclose(file);return NULL;}
    if(fread(bytes,1,length,file)!=length || fgetc(file)!=EOF || ferror(file)){
        diagnostic(error,cap,"container read failed or file changed while reading");free(bytes);fclose(file);return NULL;}
    fclose(file);result=amalur_blob_parse(bytes,length,limits,error,cap);free(bytes);return result;
}
void amalur_blob_destroy(amalur_blob *b){if(b){free(b->sorted_slots);free(b->file);free(b);}}
const unsigned char *amalur_blob_file_bytes(const amalur_blob *b,size_t *length){if(length)*length=b?b->file_size:0;return b?b->file:NULL;}
const unsigned char *amalur_blob_payload(const amalur_blob *b,uint32_t *length){if(length)*length=b?b->payload_size:0;return b?b->file+8:NULL;}
uint32_t amalur_blob_fixup_count(const amalur_blob *b){return b?b->slot_count:0;}
int amalur_blob_fixup_at(const amalur_blob *b,uint32_t index,amalur_blob_fixup *entry){
    uint32_t slot;if(!b || !entry || index>=b->slot_count)return 0;
    slot=little_u32(b->file+8+(size_t)b->payload_size+(size_t)index*4);
    entry->slot_offset=slot;entry->stored_file_offset=little_u32(b->file+8+slot);
    entry->target_offset=entry->stored_file_offset-8;return 1;
}
int amalur_blob_read_u32(const amalur_blob *b,uint32_t offset,uint32_t *value){
    if(!b || !value || b->payload_size<4 || offset>b->payload_size-4)return 0;
    *value=little_u32(b->file+8+offset);return 1;
}
int amalur_blob_read_f32(const amalur_blob *b,uint32_t offset,float *value){
    uint32_t bits;if(!value || sizeof(float)!=4 || FLT_RADIX!=2 || FLT_MANT_DIG!=24 || !amalur_blob_read_u32(b,offset,&bits))return 0;
    memcpy(value,&bits,sizeof(bits));return 1;
}
int amalur_blob_resolve_span(const amalur_blob *b,uint32_t slot,size_t count,const unsigned char **bytes,uint32_t *offset){
    uint32_t target;
    if(!b || !bytes || !registered(b,slot))return 0;
    target=little_u32(b->file+8+slot)-8;
    if(count>(size_t)(b->payload_size-target))return 0;
    *bytes=b->file+8+target;if(offset)*offset=target;return 1;
}
