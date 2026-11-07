#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
typedef struct{void**vtbl;volatile long ref;int kind;} obj;
typedef struct{uint64_t buf,mem;uint8_t*ptr;} vk_buffer;
typedef struct{obj o;uint32_t size,usage,bind,cpu,misc,stride;int ring;uint8_t*shadow;uint64_t ring_buf;uint32_t ring_off;uint64_t ring_frame;int dirty;vk_buffer gens[8];uint64_t gen_used[8];int ngens,cur;} oa_buffer;
int main(void){printf("{\"object\":%zu,\"buffer_size\":%zu,\"vk_buffer_size\":%zu,\"size\":%zu,\"ring\":%zu,\"gens\":%zu,\"ngens\":%zu,\"cur\":%zu,\"mapped_ptr_in_gen\":%zu}\n",sizeof(obj),sizeof(oa_buffer),sizeof(vk_buffer),offsetof(oa_buffer,size),offsetof(oa_buffer,ring),offsetof(oa_buffer,gens),offsetof(oa_buffer,ngens),offsetof(oa_buffer,cur),offsetof(vk_buffer,ptr));return 0;}
