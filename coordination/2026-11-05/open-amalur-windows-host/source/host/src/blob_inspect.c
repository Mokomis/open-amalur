#include "amalur_blob.h"
#include <stdio.h>
#include <string.h>

static void string_json(const char *s){unsigned char c;putchar('"');while((c=(unsigned char)*s++)){
    if(c=='"'||c=='\\'){putchar('\\');putchar(c);}else if(c<32||c>=127)printf("\\u%04x",(unsigned)c);else putchar(c);}putchar('"');}
int main(int argc,char **argv){
    amalur_blob *b;char error[256];uint32_t payload,i;size_t length;int full;
    if(argc<2||argc>3||(argc==3&&strcmp(argv[2],"--slots"))){fprintf(stderr,"Usage: amalur-blob-inspect FILE [--slots]\n");return 2;}
    full=argc==3;b=amalur_blob_load_file(argv[1],NULL,error,sizeof(error));
    if(!b){printf("{\"ok\":false,\"error\":");string_json(error);puts("}");return 1;}
    amalur_blob_payload(b,&payload);amalur_blob_file_bytes(b,&length);
    printf("{\"ok\":true,\"profile\":\"candidate-relative-u32-blob\",\"semantic_scene_decoded\":false,\"file_bytes\":%lu,\"payload_bytes\":%u,\"fixup_slots\":%u,\"pointer_bits\":%u",
           (unsigned long)length,(unsigned)payload,(unsigned)amalur_blob_fixup_count(b),(unsigned)(sizeof(void*)*8));
    if(full){printf(",\"slots\":[");for(i=0;i<amalur_blob_fixup_count(b);i++){
        amalur_blob_fixup entry;amalur_blob_fixup_at(b,i,&entry);if(i)putchar(',');
        printf("{\"slot_offset\":%u,\"target_offset\":%u}",(unsigned)entry.slot_offset,(unsigned)entry.target_offset);}putchar(']');}
    puts("}");amalur_blob_destroy(b);return 0;
}
