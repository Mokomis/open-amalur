/* Fixed callback verification. aa0850 was statically checked first: for tag0
 * in the synthetic function object it only reads wrapper/state/base metadata
 * and returns0. e43060 ignores that value and writes one TValue. No VM startup.
 */
#define main amalur_v06_baseline_main_not_called
#include "../v06-compare/native_vm_harness.c"
#undef main

static int run_empty_handle(Callback callback,uint32_t id) {
    unsigned char state_storage[0xa0],state_expected[0xa0],function_object[0x40],function_expected[0x40];
    TValue frame[24],frame_expected[24],*base=frame+2,*top=base+id;
    unsigned char *state=state_storage+0x10;void *state_pointer=state;
    uint32_t returned=0,i;int state_ok,frame_ok,function_ok,wrapper_ok,ok;
    memset(state_storage,0xa0+(int)id,sizeof(state_storage));
    memset(function_object,0,sizeof(function_object));
    for(i=0;i<24;i++){frame[i].tag=0xa5a50000u+(id<<8)+i;frame[i].payload=0x5a5a0000u+(id<<8)+i;}
    base[-1].payload=(uint32_t)(uintptr_t)function_object;
    *(TValue**)(state+0x24)=top;*(TValue**)(state+0x28)=base;
    *(TValue**)(state+0x2c)=frame+23;*(TValue**)(state+0x30)=frame;
    *(void**)(state+0x50)=&state_pointer;
    /* Helper sees function_object+0x18 low tag0, so no object payload path. */
    memcpy(state_expected,state_storage,sizeof(state_storage));
    *(TValue**)(state_expected+0x10+0x24)=top+1;
    memcpy(frame_expected,frame,sizeof(frame));frame_expected[2+id].tag=0xfb;frame_expected[2+id].payload=0;
    memcpy(function_expected,function_object,sizeof(function_object));
    vm_fault_code=0;exception_ip=0;
    __try {returned=callback(state);} __except(fault_filter(GetExceptionInformation())) {}
    state_ok=!memcmp(state_storage,state_expected,sizeof(state_storage));
    frame_ok=!memcmp(frame,frame_expected,sizeof(frame));
    function_ok=!memcmp(function_object,function_expected,sizeof(function_object));
    wrapper_ok=state_pointer==state;
    ok=!vm_fault_code&&returned==1&&state_ok&&frame_ok&&function_ok&&wrapper_ok;
    printf("%s{\"id\":%u,\"initial_stack_values\":%u,\"headroom_values\":%u,\"helper_function_tag\":0,\"returned_count\":%u,\"written_raw_lo\":\"%08x\",\"written_raw_hi\":\"%08x\",\"state_only_top_changed_by_8\":%s,\"stack_only_one_value_changed\":%s,\"helper_object_unchanged\":%s,\"wrapper_unchanged\":%s,\"exception_code\":\"%08lx\",\"exception_ip\":\"%08lx\",\"ok\":%s}",
        id?",":"",id,id,21-id,returned,top->tag,top->payload,state_ok?"true":"false",frame_ok?"true":"false",
        function_ok?"true":"false",wrapper_ok?"true":"false",vm_fault_code,(unsigned long)exception_ip,ok?"true":"false");
    fflush(stdout);return !ok;
}

int main(int argc,char **argv) {
    unsigned char *file,*image;size_t length;void *reservation;Callback callback;
    uint32_t i;int failures=0,unchanged;
    if(sizeof(void*)!=4)return fail("empty-handle harness requires x86");
    if(argc!=2)return fail("usage: native_empty_handle_harness.exe koa.exe");
    reservation=reserve_image_first(argv[1]);if(!reservation)return fail("reserve isolated image");
    file=readfile(argv[1],&length);if(!file)return fail("read original image");
    if(!hash_ok(file,length)){free(file);return fail("original SHA256 mismatch");}
    image=map_image(file,length,reservation);free(file);if(!image)return fail("map original image");
    callback=(Callback)(image+0xe43060-0x400000);
    printf("{\"schema\":\"amalur-original-empty-handle-x86-v1\",\"target_sha256\":\"%s\",\"callback_address\":\"0x00e43060\",\"helper_address\":\"0x00aa0850\",\"mapped_image_base\":\"%08x\",\"relocation_delta\":\"%08x\",\"highlow_relocations\":%u,\"pe_entry_invoked\":false,\"tls_invoked\":false,\"imports_resolved\":false,\"cases\":[",
        expected_sha,(uint32_t)(uintptr_t)image,relocation_delta,relocation_count);
    for(i=0;i<8;i++)failures+=run_empty_handle(callback,i);
    file=readfile(argv[1],&length);unchanged=file&&hash_ok(file,length);free(file);
    printf("],\"cases_executed\":8,\"failed_cases\":%d,\"original_file_unchanged\":%s}\n",failures,unchanged?"true":"false");
    VirtualFree(image,0,MEM_RELEASE);return failures||!unchanged?1:0;
}
