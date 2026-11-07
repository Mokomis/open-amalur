/* Standalone serialized FAB pose probe. No PE entrypoint, TLS, imports, game
 * startup, graphics/device path or original-process attachment.
 * Usage: barrel_native_pose koa.exe barrel.fab_bxml output.bin
 * Calls only reviewed 00c9a9b0 pose conversion/composition kernel and00ac3a70 matrix.
 * Output:u32 count; each bone48-byte internal transform followed by16 matrix floats.
 */
#include <windows.h>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <vector>
typedef unsigned char u8;typedef unsigned short u16;typedef unsigned int u32;
static std::vector<u8> read_all(const char*p){FILE*f=fopen(p,"rb");if(!f){fprintf(stderr,"open %s\n",p);exit(2);}fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);std::vector<u8>b((size_t)n);if(fread(b.data(),1,(size_t)n,f)!=(size_t)n)exit(2);fclose(f);return b;}
static u8*rel(u8*a,int o){int v=*(int*)(a+o);return v?a+o+v:0;}
static LONG WINAPI on_fault(EXCEPTION_POINTERS*e){fprintf(stderr,"fault code %08lx at %p addr %p\n",e->ExceptionRecord->ExceptionCode,e->ExceptionRecord->ExceptionAddress,(void*)e->ExceptionRecord->ExceptionInformation[1]);ExitProcess(9);return 0;}
/* The fixed image range must be claimed before the loader's heaps grow into it. */
static const size_t IMAGE_RESERVE=0x1F00000;
static int launch(const char*self,int argc,char**argv){
 char cmd[4096];snprintf(cmd,sizeof cmd,"\"%s\" --child",self);for(int i=1;i<argc;i++){strncat(cmd," \"",sizeof cmd-strlen(cmd)-1);strncat(cmd,argv[i],sizeof cmd-strlen(cmd)-1);strncat(cmd,"\"",sizeof cmd-strlen(cmd)-1);}
 STARTUPINFOA si={sizeof si};PROCESS_INFORMATION pi;if(!CreateProcessA(self,cmd,0,0,TRUE,CREATE_SUSPENDED,0,0,&si,&pi)){fprintf(stderr,"create %lu\n",GetLastError());return 4;}
 void*r=VirtualAllocEx(pi.hProcess,(void*)0x400000,IMAGE_RESERVE,MEM_RESERVE,PAGE_EXECUTE_READWRITE);
 if(r!=(void*)0x400000){MEMORY_BASIC_INFORMATION m;SIZE_T at=0x10000;while(at<0x2400000&&VirtualQueryEx(pi.hProcess,(void*)at,&m,sizeof m)){if(m.State!=MEM_FREE)fprintf(stderr,"used %p %zx\n",m.BaseAddress,m.RegionSize);at=(SIZE_T)m.BaseAddress+m.RegionSize;}TerminateProcess(pi.hProcess,4);fprintf(stderr,"reserve failed %lu\n",GetLastError());return 4;}
 ResumeThread(pi.hThread);WaitForSingleObject(pi.hProcess,INFINITE);DWORD code=9;GetExitCodeProcess(pi.hProcess,&code);return (int)code;
}
int main(int argc,char**argv){
 if(argc==4)return launch(argv[0],argc,argv);
 if(argc!=5||strcmp(argv[1],"--child"))return 2;argv++;argc--;SetUnhandledExceptionFilter(on_fault);
 std::vector<u8>b=read_all(argv[1]);
 IMAGE_NT_HEADERS32*nt=(IMAGE_NT_HEADERS32*)(b.data()+((IMAGE_DOS_HEADER*)b.data())->e_lfanew);
 if(nt->FileHeader.Machine!=IMAGE_FILE_MACHINE_I386||nt->OptionalHeader.ImageBase!=0x400000)return 3;
 u8*image=nt->OptionalHeader.SizeOfImage<=IMAGE_RESERVE?(u8*)VirtualAlloc((void*)0x400000,nt->OptionalHeader.SizeOfImage,MEM_COMMIT,PAGE_EXECUTE_READWRITE):0;
 if(image!=(u8*)0x400000){fprintf(stderr,"image range unavailable size %lx err %lu\n",nt->OptionalHeader.SizeOfImage,GetLastError());return 4;}
 IMAGE_SECTION_HEADER*s=IMAGE_FIRST_SECTION(nt);
 for(unsigned i=0;i<nt->FileHeader.NumberOfSections;i++)memcpy(image+s[i].VirtualAddress,b.data()+s[i].PointerToRawData,s[i].SizeOfRawData);

 // Invoke only the reviewed FAB pose conversion/parent composition kernel.
 std::vector<u8>sf=read_all(argv[2]);u8*skel=sf.data()+4;
 if(*(u32*)skel!=0x45533033)return 5;
 u32 n=*(u16*)(skel+0x10);
 u8 base[0x20]={0};*(u8**)(base+0x18)=skel;
 u8*world=(u8*)_aligned_malloc(n*48,16);memset(world,0,n*48);
 struct Array{u8*p;u32 n,capacity;u16 kind,grow;} arr={world,n,n,0x35,0xffff};
 typedef void (__thiscall *compose_fn)(void*,void*,float);
 typedef void (__fastcall *matrix_fn)(void*,void*,float*);
 ((compose_fn)0xc9a9b0)(&arr,base,1.f);
 FILE*f=fopen(argv[3],"wb");if(!f)return 2;fwrite(&n,4,1,f);
 for(u32 i=0;i<n;i++){
  float mat[16]={0};((matrix_fn)0xac3a70)(world+i*48,0,mat);
  fwrite(world+i*48,48,1,f);fwrite(mat,64,1,f);
 }
 fclose(f);printf("joints %u; native serialized-pose conversion and parent composition done\n",n);return 0;
}
