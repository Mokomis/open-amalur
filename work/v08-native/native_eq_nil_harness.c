/* Narrow original-VM EQ experiment. Reuse the established read-only PE mapper
 * unchanged; the baseline main is renamed and never called. This executable
 * accepts no fixture file and runs only the fixed EQ/LOADBOOL/RETURN templates.
 * No PE entry, imports, TLS, allocator, engine services or game saves are used.
 */
#define main amalur_v06_baseline_main_not_called
#include "../v06-compare/native_vm_harness.c"
#undef main

static uint32_t eq_word(uint32_t op,uint32_t a,uint32_t b,uint32_t c) {
    return (op<<25)|a|(((b<<9)|c)<<8);
}
static int run_eq_nil(VM vm,uint32_t id,uint32_t raw_lo,uint32_t raw_hi,
                      int reverse,int polarity,int nil_control) {
    uint32_t code[9]={0};TValue frame[7],constants[1],*base=frame+1,*result=NULL;
    TValue left,right;unsigned char state[0x80],function[0x40];
    uint32_t returned=0,expected=nil_control?(uint32_t)polarity:(uint32_t)!polarity;
    int ok=1,unchanged=0;
    memset(frame,0,sizeof(frame));memset(constants,0,sizeof(constants));
    memset(state,0,sizeof(state));memset(function,0,sizeof(function));
    left.tag=nil_control?0:raw_lo;left.payload=nil_control?0:raw_hi;right.tag=0;right.payload=0;
    if(reverse){TValue temporary=left;left=right;right=temporary;}
    base[0]=left;base[1]=right;
    code[0]=eq_word(4,(uint32_t)polarity,0,1); /* native EQ R0,R1 */
    code[1]=(28u<<25)|(65536u<<8);           /* PC1 JMP -> PC3 */
    code[2]=eq_word(13,2,0,1);              /* false, skip true */
    code[3]=eq_word(13,2,1,0);              /* true */
    code[4]=eq_word(9,2,2,0);               /* RETURN R2, one result */
    *(TValue**)(state+0x24)=base+3;*(TValue**)(state+0x28)=base;
    *(TValue**)(state+0x2c)=base+5;*(TValue**)(state+0x30)=frame;
    *(TValue**)(function+0x11)=constants;*(uint16_t*)(function+0x19)=3;
    frame[0].tag=9;frame[0].payload=(uint32_t)(uintptr_t)function;
    vm_fault_code=0;exception_ip=0;
    __try {
        returned=vm(state,code,0);result=*(TValue**)(state+0x24)-returned;
        unchanged=!memcmp(base,&left,sizeof(left))&&!memcmp(base+1,&right,sizeof(right));
        if(returned!=1||result!=base+2||result->tag!=1||result->payload!=expected||!unchanged)ok=0;
    } __except(fault_filter(GetExceptionInformation())) {ok=0;}
    printf("%s{\"id\":%u,\"scope\":\"%s\",\"left_raw_lo\":\"%08x\",\"left_raw_hi\":\"%08x\",\"right_raw_lo\":\"%08x\",\"right_raw_hi\":\"%08x\",\"branch_A\":%d,\"expected_boolean\":%u,\"ok\":%s,\"input_registers_unchanged\":%s,\"result_count\":%u,\"exception_code\":\"%08lx\",\"exception_ip\":\"%08lx\"",
        id?",":"",id,nil_control?"nil-equals-nil-control":"tag11-versus-nil",left.tag,left.payload,right.tag,right.payload,polarity,expected,ok?"true":"false",unchanged?"true":"false",returned,vm_fault_code,(unsigned long)exception_ip);
    if(!vm_fault_code&&returned==1&&result==base+2)
        printf(",\"result_raw_lo\":\"%08x\",\"result_raw_hi\":\"%08x\"",result->tag,result->payload);
    printf("}");fflush(stdout);return !ok;
}

int main(int argc,char **argv) {
    static const uint32_t lows[]={0x0000000b,0x1234567b,0x8000000b,0xfffffffb};
    static const uint32_t highs[]={0x00000000,0x00000001,0x80000000,0xffffffff};
    unsigned char *file,*image;size_t length;void *reservation;VM vm;
    uint32_t i,j,id=0;int order,polarity,failures=0,unchanged;
    if(sizeof(void*)!=4)return fail("EQ harness requires x86");
    if(argc!=2)return fail("usage: native_eq_nil_harness.exe koa.exe");
    reservation=reserve_image_first(argv[1]);if(!reservation)return fail("reserve isolated image");
    file=readfile(argv[1],&length);if(!file)return fail("read original image");
    if(!hash_ok(file,length)){free(file);return fail("original SHA256 mismatch");}
    image=map_image(file,length,reservation);free(file);if(!image)return fail("map original image");
    vm=(VM)(image+0x10adce0-0x400000);
    printf("{\"schema\":\"amalur-original-eq-tag11-nil-x86-v1\",\"target_sha256\":\"%s\",\"mapped_image_base\":\"%08x\",\"relocation_delta\":\"%08x\",\"highlow_relocations\":%u,\"pe_entry_invoked\":false,\"tls_invoked\":false,\"imports_resolved\":false,\"fixed_opcode_template\":[4,28,13,13,9],\"cases\":[",
        expected_sha,(uint32_t)(uintptr_t)image,relocation_delta,relocation_count);
    for(i=0;i<4;i++)for(j=0;j<4;j++)for(order=0;order<2;order++)for(polarity=0;polarity<2;polarity++)
        failures+=run_eq_nil(vm,id++,lows[i],highs[j],order,polarity,0);
    for(polarity=0;polarity<2;polarity++)failures+=run_eq_nil(vm,id++,0,0,0,polarity,1);
    file=readfile(argv[1],&length);unchanged=file&&hash_ok(file,length);free(file);
    printf("],\"cases_executed\":%u,\"failed_cases\":%d,\"original_file_unchanged\":%s}\n",id,failures,unchanged?"true":"false");
    VirtualFree(image,0,MEM_RELEASE);return failures||!unchanged?1:0;
}
