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

typedef uint32_t (__cdecl *HashFn)(const char*,uint32_t*,uint32_t);
static uint32_t authored_hash(const char *s,uint32_t seed,const uint32_t *table,int fold){
 size_t n=strlen(s),i;uint32_t out=seed;
 for(i=0;i<n;i++){unsigned c=(unsigned char)s[i];if(fold&&c>='A'&&c<='Z')c+=32;out+=table[i%50]*c+table[c%50]*(uint32_t)(i+1);}return out;
}
int main(int argc,char **argv){
 unsigned char *file,*image;size_t size;void *reservation;HashFn hash;uint32_t *table;unsigned i,failures=0,cases=0;
 const char *names[]={"","a","A","none","NONE","LedgerLaunchMap","ledgerlaunchmap","SpaceCommon","INPUT_ACTION_KEY","int_dal_gorhart_alchemistshop","a/b\\c_01","!@#$%^&*()_+-= {}[];:,.?","0123456789"};char generated[260];
 if(argc!=2)return fail("expected immutable game executable path");
 reservation=reserve_image_first(argv[1]);if(!reservation)return fail("reserve");file=readfile(argv[1],&size);
 if(!file||!hash_ok(file,size))return fail("identity");image=map_image(file,size,reservation);free(file);if(!image)return fail("mapping");
 if(*(uint32_t*)(image+0x1a0bec0-0x400000)!=0)return fail("native lowercase locale mode differs from admitted ASCII default");
 table=(uint32_t*)(image+0x1721040-0x400000);hash=(HashFn)(image+0xaf08b0-0x400000);
 printf("{\"scope\":\"original hash and ASCII lowercase routines in isolated x86 mapped image; no PE entry, TLS, imports or game launch\",\"cases\":[");
 for(i=0;i<sizeof(names)/sizeof(names[0])+20;i++){
  const char *s;uint32_t seed,exact=0,folded=0,expected_exact,expected_folded;int success=1;unsigned j;
  if(i<sizeof(names)/sizeof(names[0]))s=names[i];else{unsigned n=(i-(unsigned)(sizeof(names)/sizeof(names[0])))*13+1;for(j=0;j<n;j++)generated[j]=(char)(32+(j*17+i)%95);generated[n]=0;s=generated;}
  seed=(i%3==0)?0xFFFFFF00u:0;expected_exact=authored_hash(s,seed,table,0);expected_folded=authored_hash(s,seed,table,1);
  __try{exact=hash(s,&folded,seed);}__except(fault_filter(GetExceptionInformation())){success=0;}
  if(!success||exact!=expected_exact||folded!=expected_folded)failures++;
  if(cases++)putchar(',');printf("{\"id\":%u,\"bytes\":%u,\"seed\":%u,\"exact\":%u,\"folded\":%u,\"expected_exact\":%u,\"expected_folded\":%u,\"executed\":%s}",i,(unsigned)strlen(s),seed,exact,folded,expected_exact,expected_folded,success?"true":"false");
 }
 printf("],\"failed_cases\":%u,\"target_sha256\":\"%s\"}\n",failures,expected_sha);VirtualFree(image,0,MEM_RELEASE);return failures?1:0;
}
