/* Execute selected original Amalur VM instructions in an isolated x86 process.
 * No PE entrypoint, TLS callback, import resolver, game allocator or save code.
 * Original image uses standard PE HIGHLOW base relocations only. Only synthetic primitive
 * bytecode admitted below; exceptions are reported, not suppressed as success.
 */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <bcrypt.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#pragma comment(lib, "bcrypt.lib")

static const char expected_sha[]="16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314";
typedef struct { uint32_t tag, payload; } TValue;
typedef uint32_t (__cdecl *VM)(void *, uint32_t *, int);
typedef uint32_t (__cdecl *Callback)(void *);
static DWORD vm_fault_code; static uintptr_t exception_ip;
static uint32_t relocation_delta, relocation_count;
static int fault_filter(EXCEPTION_POINTERS *p) {
    vm_fault_code=p->ExceptionRecord->ExceptionCode;
    exception_ip=(uintptr_t)p->ExceptionRecord->ExceptionAddress;
    return EXCEPTION_EXECUTE_HANDLER;
}
static int fail(const char *s) { fprintf(stderr,"native_vm_harness: %s (WinError %lu)\n",s,GetLastError()); return 2; }
static unsigned char *readfile(const char *name, size_t *len) {
    FILE *f=NULL; unsigned char *data; long n;
    if(fopen_s(&f,name,"rb") || !f) return NULL;
    if(fseek(f,0,SEEK_END) || (n=ftell(f))<0 || n>64*1024*1024 || fseek(f,0,SEEK_SET)) {fclose(f);return NULL;}
    data=(unsigned char*)malloc((size_t)n); if(!data){fclose(f);return NULL;}
    if(fread(data,1,(size_t)n,f)!=(size_t)n){free(data);fclose(f);return NULL;}
    fclose(f);*len=(size_t)n;return data;
}
static int hash_ok(const unsigned char *p,size_t n) {
    BCRYPT_ALG_HANDLE alg=NULL; BCRYPT_HASH_HANDLE hash=NULL; DWORD objlen=0,got=0;
    unsigned char digest[32],*obj=NULL; char hex[65]; int ok=0; unsigned i;
    if(BCryptOpenAlgorithmProvider(&alg,BCRYPT_SHA256_ALGORITHM,NULL,0)<0)goto done;
    if(BCryptGetProperty(alg,BCRYPT_OBJECT_LENGTH,(PUCHAR)&objlen,sizeof(objlen),&got,0)<0)goto done;
    obj=(unsigned char*)malloc(objlen);if(!obj)goto done;
    if(BCryptCreateHash(alg,&hash,obj,objlen,NULL,0,0)<0)goto done;
    if(BCryptHashData(hash,(PUCHAR)p,(ULONG)n,0)<0 || BCryptFinishHash(hash,digest,32,0)<0)goto done;
    for(i=0;i<32;i++)sprintf_s(hex+i*2,3,"%02x",digest[i]);hex[64]=0;
    ok=!strcmp(hex,expected_sha);
done:
    if(hash)BCryptDestroyHash(hash);if(alg)BCryptCloseAlgorithmProvider(alg,0);free(obj);return ok;
}
static void diagnose_mapping(void) {
    uintptr_t pos=0x400000;MEMORY_BASIC_INFORMATION m;
    while(pos<0x4400000 && VirtualQuery((void*)pos,&m,sizeof(m))) {
        fprintf(stderr,"region base=%08lx allocation=%08lx size=%08lx state=%08lx type=%08lx protect=%08lx\n",(unsigned long)(uintptr_t)m.BaseAddress,(unsigned long)(uintptr_t)m.AllocationBase,(unsigned long)m.RegionSize,m.State,m.Type,m.Protect);
        if((uintptr_t)m.BaseAddress+m.RegionSize<=pos)break;pos=(uintptr_t)m.BaseAddress+m.RegionSize;
    }
}
static void *reserve_image_first(const char *name) {
    unsigned char header[4096];DWORD got=0;HANDLE f;IMAGE_DOS_HEADER *dos;IMAGE_NT_HEADERS32 *nt;void *region;
    f=CreateFileA(name,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
    if(f==INVALID_HANDLE_VALUE)return NULL;
    if(!ReadFile(f,header,sizeof(header),&got,NULL)){CloseHandle(f);return NULL;}CloseHandle(f);
    if(got<sizeof(IMAGE_DOS_HEADER))return NULL;dos=(IMAGE_DOS_HEADER*)header;
    if(dos->e_magic!=IMAGE_DOS_SIGNATURE || dos->e_lfanew<0 || (size_t)dos->e_lfanew+sizeof(*nt)>got)return NULL;
    nt=(IMAGE_NT_HEADERS32*)(header+dos->e_lfanew);
    if(nt->Signature!=IMAGE_NT_SIGNATURE || nt->OptionalHeader.ImageBase!=0x400000 || nt->OptionalHeader.SizeOfImage>64*1024*1024)return NULL;
    region=VirtualAlloc((void*)0x10000000,nt->OptionalHeader.SizeOfImage,MEM_RESERVE,PAGE_NOACCESS);
    if(!region)region=VirtualAlloc(NULL,nt->OptionalHeader.SizeOfImage,MEM_RESERVE,PAGE_NOACCESS);
    if(!region)diagnose_mapping();return region;
}
static unsigned char *map_image(const unsigned char *file,size_t n,void *reservation) {
    const IMAGE_DOS_HEADER *dos;const IMAGE_NT_HEADERS32 *nt;const IMAGE_SECTION_HEADER *s;
    unsigned char *base;unsigned i;DWORD old;
    if(n<sizeof(IMAGE_DOS_HEADER))return NULL;dos=(const IMAGE_DOS_HEADER*)file;
    if(dos->e_magic!=IMAGE_DOS_SIGNATURE || dos->e_lfanew<0 || (size_t)dos->e_lfanew+sizeof(*nt)>n)return NULL;
    nt=(const IMAGE_NT_HEADERS32*)(file+dos->e_lfanew);
    if(nt->Signature!=IMAGE_NT_SIGNATURE || nt->FileHeader.Machine!=IMAGE_FILE_MACHINE_I386 || nt->OptionalHeader.Magic!=IMAGE_NT_OPTIONAL_HDR32_MAGIC || nt->OptionalHeader.ImageBase!=0x400000 || nt->OptionalHeader.SizeOfImage>64*1024*1024 || nt->OptionalHeader.SizeOfHeaders>n)return NULL;
    s=IMAGE_FIRST_SECTION(nt);if((const unsigned char*)(s+nt->FileHeader.NumberOfSections)>file+n)return NULL;
    base=(unsigned char*)VirtualAlloc(reservation,nt->OptionalHeader.SizeOfImage,MEM_COMMIT,PAGE_READWRITE);
    if(!base)return NULL;memcpy(base,file,nt->OptionalHeader.SizeOfHeaders);
    for(i=0;i<nt->FileHeader.NumberOfSections;i++) {
        if((uint64_t)s[i].PointerToRawData+s[i].SizeOfRawData>n || (uint64_t)s[i].VirtualAddress+s[i].SizeOfRawData>nt->OptionalHeader.SizeOfImage)goto bad;
        memcpy(base+s[i].VirtualAddress,file+s[i].PointerToRawData,s[i].SizeOfRawData);
    }
    relocation_delta=(uint32_t)(uintptr_t)base-nt->OptionalHeader.ImageBase;relocation_count=0;
    if(relocation_delta) {
        IMAGE_DATA_DIRECTORY dir=nt->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_BASERELOC];uint32_t at=0;
        if(!dir.VirtualAddress || !dir.Size || (uint64_t)dir.VirtualAddress+dir.Size>nt->OptionalHeader.SizeOfImage)goto bad;
        while(at<dir.Size) {
            IMAGE_BASE_RELOCATION *block;uint32_t entries,j;WORD *fixups;
            if(dir.Size-at<sizeof(IMAGE_BASE_RELOCATION))goto bad;
            block=(IMAGE_BASE_RELOCATION*)(base+dir.VirtualAddress+at);
            if(block->SizeOfBlock<sizeof(*block) || block->SizeOfBlock>dir.Size-at || (block->SizeOfBlock-sizeof(*block))%2)goto bad;
            entries=(block->SizeOfBlock-sizeof(*block))/2;fixups=(WORD*)(block+1);
            for(j=0;j<entries;j++) {
                uint32_t type=fixups[j]>>12,rva=block->VirtualAddress+(fixups[j]&0xfff);
                if(type==IMAGE_REL_BASED_ABSOLUTE)continue;
                if(type!=IMAGE_REL_BASED_HIGHLOW || (uint64_t)rva+4>nt->OptionalHeader.SizeOfImage)goto bad;
                *(uint32_t*)(base+rva)+=relocation_delta;relocation_count++;
            }
            at+=block->SizeOfBlock;
        }
    }
    if(!VirtualProtect(base,nt->OptionalHeader.SizeOfImage,PAGE_NOACCESS,&old))goto bad;
    if(!VirtualProtect(base,nt->OptionalHeader.SizeOfHeaders,PAGE_READONLY,&old))goto bad;
    for(i=0;i<nt->FileHeader.NumberOfSections;i++) {
        DWORD flags=s[i].Characteristics,protect=PAGE_READONLY;
        SIZE_T len=s[i].Misc.VirtualSize>s[i].SizeOfRawData?s[i].Misc.VirtualSize:s[i].SizeOfRawData;
        if(flags&IMAGE_SCN_MEM_EXECUTE)protect=(flags&IMAGE_SCN_MEM_WRITE)?PAGE_EXECUTE_READWRITE:PAGE_EXECUTE_READ;
        else if(flags&IMAGE_SCN_MEM_WRITE)protect=PAGE_READWRITE;
        if(len && !VirtualProtect(base+s[i].VirtualAddress,len,protect,&old))goto bad;
    }
    FlushInstructionCache(GetCurrentProcess(),base,nt->OptionalHeader.SizeOfImage);return base;
bad:VirtualFree(base,0,MEM_RELEASE);return NULL;
}
/* Authored callees are controlled boundary inputs; the VM call/setup/result
 * movement under comparison still executes the original game instructions. */
static uint32_t __cdecl cb_empty(void *state) {(void)state;return 0;}
static uint32_t __cdecl cb_nil(void *state) {
    TValue *top=*(TValue**)((unsigned char*)state+0x24);top->tag=0;top->payload=0;
    *(TValue**)((unsigned char*)state+0x24)=top+1;return 1;
}
static uint32_t __cdecl cb_multi(void *state) {
    TValue *top=*(TValue**)((unsigned char*)state+0x24);
    top[0].tag=0;top[0].payload=0;top[1].tag=3;top[1].payload=7;
    top[2].tag=1;top[2].payload=0;top[3].tag=0;top[3].payload=0;
    *(TValue**)((unsigned char*)state+0x24)=top+4;return 4;
}
static uint32_t __cdecl cb_echo(void *state) {
    return (uint32_t)(*(TValue**)((unsigned char*)state+0x24)-*(TValue**)((unsigned char*)state+0x28));
}
static uint32_t __cdecl cb_count_echo(void *state) {
    TValue *base=*(TValue**)((unsigned char*)state+0x28),*top=*(TValue**)((unsigned char*)state+0x24);uint32_t n=(uint32_t)(top-base);
    top[0].tag=3;top[0].payload=n;memmove(top+1,base,n*sizeof(TValue));
    *(TValue**)((unsigned char*)state+0x24)=top+n+1;return n+1;
}
static Callback callback_for(uint32_t id,unsigned char *image) {
    switch(id) {
        case 1:return cb_empty;case 2:return cb_nil;case 3:return cb_multi;
        case 4:return cb_echo;case 5:return cb_count_echo;
        case 0xaa1fa0:case 0xaa1fd0:case 0xaa20b0:case 0xaa2100:case 0xaa2160:return (Callback)(image+id-0x400000);
    }return NULL;
}
static int allowed(uint32_t op) {
    switch(op) {
        case 1:case 4:case 5:case 7:case 9:case 13:case 25:case 26:case 28:
        case 34:case 35:case 36:case 37:case 38:case 39:case 40:case 41:
        case 42:case 43:case 44:case 45:case 47:case 48:
        case 50:case 51:case 52:case 53:case 56:case 57:case 65:case 66:return 1;
    }return 0;
}
static int get32(const unsigned char **p,const unsigned char *end,uint32_t *out) {
    if((size_t)(end-*p)<4)return 0;memcpy(out,*p,4);*p+=4;return 1;
}
static int getbytes(const unsigned char **p,const unsigned char *end,void *dst,size_t n) {
    if((size_t)(end-*p)<n)return 0;memcpy(dst,*p,n);*p+=n;return 1;
}
int main(int argc,char **argv) {
    unsigned char *file,*fixtures,*image;size_t size,fixture_size;const unsigned char *p,*end;
    uint32_t count,k;VM vm;int failures=0,callbacks=0,call_mode=0;void *reservation;
    if(sizeof(void*)!=4)return fail("must compile x86");
    if(argc!=3)return fail("usage: native_vm_harness.exe koa.exe fixtures.bin");
    reservation=reserve_image_first(argv[1]);if(!reservation)return fail("reserve isolated relocated image range before allocations");
    file=readfile(argv[1],&size);if(!file)return fail("read original image");
    if(!hash_ok(file,size)){free(file);return fail("target SHA256 mismatch");}
    image=map_image(file,size,reservation);free(file);if(!image)return fail("map original image and apply standard HIGHLOW relocations");
    fixtures=readfile(argv[2],&fixture_size);if(!fixtures)return fail("read fixture file");
    if(fixture_size<12)return fail("bad fixture header");
    callbacks=!memcmp(fixtures,"OMCB06\0\0",8);call_mode=!memcmp(fixtures,"OMCL06\0\0",8);
    if(!callbacks && !call_mode && memcmp(fixtures,"OMVM06\0\0",8))return fail("bad fixture header");
    p=fixtures+8;end=fixtures+fixture_size;if(!get32(&p,end,&count)||count>10000)return fail("case count");
    vm=(VM)(image+(0x10adce0-0x400000));
    printf("{\"schema\":\"amalur-original-vm-native-x86-v1\",\"target_sha256\":\"%s\",\"mapped_image_base\":\"%08x\",\"relocation_delta\":\"%08x\",\"highlow_relocations\":%u,\"pe_entry_invoked\":false,\"tls_invoked\":false,\"imports_resolved\":false,\"cases\":[",expected_sha,(uint32_t)(uintptr_t)image,relocation_delta,relocation_count);
    for(k=0;k<count;k++) {
        uint32_t id,ncode,nregs,nconst,ninit,i,returned=0;int ok=1;
        uint32_t *code;TValue *frame,*base,*constants,*result=NULL;
        unsigned char state[0x80],function[0x40],closures[190][0x20],callframes[32][0x10];
        uint32_t capacity;
        if(!get32(&p,end,&id)||!get32(&p,end,&ncode)||!get32(&p,end,&nregs)||!get32(&p,end,&nconst)||!get32(&p,end,&ninit))return fail("truncated case header");
        if(!ncode||ncode>5000||!nregs||nregs>190||nconst>256||ninit>nregs)return fail("fixture bounds");
        capacity=nregs+(call_mode?128:0);
        code=(uint32_t*)calloc(ncode+4,4);frame=(TValue*)calloc(capacity+3,sizeof(TValue));constants=(TValue*)calloc(nconst+1,sizeof(TValue));
        if(!code||!frame||!constants)return fail("fixture allocations");base=frame+1;
        if(!getbytes(&p,end,code,ncode*4)||!getbytes(&p,end,base,ninit*8)||!getbytes(&p,end,constants,nconst*8))return fail("truncated fixture");
        if(callbacks) {
            if(ncode!=1 || nconst || !ninit || nregs<=ninit)return fail("callback fixture shape");
            if(code[0]==0xaa20b0 && ninit<2)return fail("pow callback requires two numeric inputs");
            for(i=0;i<ninit;i++)if((base[i].tag&15)!=3)return fail("callback initial value must be int32");
            if(code[0]!=0xaa1fa0 && code[0]!=0xaa1fd0 && code[0]!=0xaa20b0 && code[0]!=0xaa2100 && code[0]!=0xaa2160)return fail("callback outside native math allowlist");
        } else for(i=0;i<ncode;i++) {
            uint32_t op=code[i]>>25;
            if(!allowed(op) && !(call_mode && (op==2||op==3||op==22||op==23||op==62||op==63)))return fail("opcode outside isolated fixture allowlist");
        }
        memset(closures,0,sizeof(closures));
        for(i=0;i<ninit;i++) {
            uint32_t tag=base[i].tag&15;
            if(call_mode && tag==10) {
                Callback cb=callback_for(base[i].payload,image);if(!cb)return fail("seeded callback ID outside allowlist");
                *(Callback*)(closures[i]+8)=cb;base[i].payload=(uint32_t)(uintptr_t)closures[i];
            } else if(tag!=0&&tag!=1&&tag!=3)return fail("initial value outside primitive domain");
        }
        for(i=0;i<nconst;i++)if((constants[i].tag&15)!=0&&(constants[i].tag&15)!=1&&(constants[i].tag&15)!=3)return fail("constant outside primitive domain");
        memset(state,0,sizeof(state));memset(function,0,sizeof(function));memset(callframes,0,sizeof(callframes));
        if(call_mode){*(void**)(state+0xc)=callframes;*(void**)(state+0x10)=callframes+31;*(void**)(state+0x14)=callframes;}
        *(TValue**)(state+0x24)=base+(callbacks?ninit:nregs);*(TValue**)(state+0x28)=base;*(TValue**)(state+0x2c)=base+capacity+1;*(TValue**)(state+0x30)=frame;
        *(TValue**)(function+0x11)=constants;*(uint16_t*)(function+0x19)=(uint16_t)nregs;
        frame[0].tag=9;frame[0].payload=(uint32_t)(uintptr_t)function;
        vm_fault_code=0;exception_ip=0;
        __try {
            returned=callbacks?((Callback)(image+(code[0]-0x400000)))(state):vm(state,code,0);
            result=*(TValue**)(state+0x24)-returned;
            if(returned>capacity || result<base || result+returned>base+capacity)ok=0;
        } __except(fault_filter(GetExceptionInformation())) {ok=0;}
        printf("%s{\"id\":%u,\"ok\":%s,\"result_count\":%u,\"exception_code\":\"%08lx\",\"exception_ip\":\"%08lx\",\"results\":[",k?",":"",id,ok?"true":"false",returned,vm_fault_code,(unsigned long)exception_ip);
        if(ok)for(i=0;i<returned;i++)printf("%s{\"tag\":%u,\"raw_lo\":\"%08x\",\"raw_hi\":\"%08x\"}",i?",":"",result[i].tag&15,result[i].tag,result[i].payload);
        printf("]}");fflush(stdout);if(!ok)failures++;
        free(code);free(frame);free(constants);
    }
    printf("],\"failed_cases\":%d}\n",failures);
    if(p!=end)return fail("fixture trailing bytes");
    free(fixtures);VirtualFree(image,0,MEM_RELEASE);return failures?1:0;
}
