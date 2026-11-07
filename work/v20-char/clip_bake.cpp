/* Standalone clip baker: no PE entrypoint, imports, game startup or device access.
 * Maps a private copy of koa.exe and invokes only the pure Edge animation decompressor 0x111bf10.
 * Usage: clip_bake koa.exe skeleton.fab_bxml clip.anm_bxml out.bin
 * Output: u32 joints, u32 frames, f32 fps, then frames*joints*(rotation xyzw, translation xyzw, scale xyzw). */
#include <windows.h>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <vector>
typedef unsigned char u8;typedef unsigned short u16;typedef unsigned int u32;
typedef void (__cdecl *decode_fn)(void*,void*,void*,void*,int,int,float);
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
 if(argc==5)return launch(argv[0],argc,argv);
 if(argc!=6||strcmp(argv[1],"--child"))return 2;argv++;argc--;SetUnhandledExceptionFilter(on_fault);
 std::vector<u8>b=read_all(argv[1]);
 IMAGE_NT_HEADERS32*nt=(IMAGE_NT_HEADERS32*)(b.data()+((IMAGE_DOS_HEADER*)b.data())->e_lfanew);
 if(nt->FileHeader.Machine!=IMAGE_FILE_MACHINE_I386||nt->OptionalHeader.ImageBase!=0x400000)return 3;
 u8*image=nt->OptionalHeader.SizeOfImage<=IMAGE_RESERVE?(u8*)VirtualAlloc((void*)0x400000,nt->OptionalHeader.SizeOfImage,MEM_COMMIT,PAGE_EXECUTE_READWRITE):0;
 if(image!=(u8*)0x400000){fprintf(stderr,"image range unavailable size %lx err %lu\n",nt->OptionalHeader.SizeOfImage,GetLastError());return 4;}
 IMAGE_SECTION_HEADER*s=IMAGE_FIRST_SECTION(nt);
 for(unsigned i=0;i<nt->FileHeader.NumberOfSections;i++)memcpy(image+s[i].VirtualAddress,b.data()+s[i].PointerToRawData,s[i].SizeOfRawData);
 decode_fn decode=(decode_fn)0x111bf10;
 std::vector<u8>sf=read_all(argv[2]);if(memcmp(sf.data()+4,"30SE",4)&&memcmp(sf.data()+4,"3" "0SE",4))return 5;
 u8*skel=sf.data()+4;u32 joints=*(u16*)(skel+0x10);u8*bind=rel(skel,0x18);
 std::vector<u8>cf=read_all(argv[3]);u32 size=*(u32*)(cf.data()+4);
 u8*anim=(u8*)_aligned_malloc(size,128);memcpy(anim,cf.data()+8,size);
 if(memcmp(anim,"50AE",4)){fprintf(stderr,"bad clip tag\n");return 5;}
 float fps=*(float*)(anim+8);u32 clipJoints=*(u16*)(anim+0xe),frames=*(u16*)(anim+0x10),sets=*(u16*)(anim+0x12);
 /* Some clips animate only the first joints of the rig; the rest stay at the bind pose each frame starts from. */
 if(clipJoints>joints){fprintf(stderr,"joint mismatch clip %u skel %u\n",clipJoints,joints);return 6;}
 u8*frameTab=rel(anim,0x3c),*dataTab=rel(anim,0x38);
 u8*out=(u8*)_aligned_malloc(joints*48+64,128);u8*user=(u8*)_aligned_malloc(4096,128);u8*work=(u8*)_aligned_malloc(1<<20,128);
 FILE*f=fopen(argv[4],"wb");if(!f)return 2;fwrite(&joints,4,1,f);fwrite(&frames,4,1,f);fwrite(&fps,4,1,f);
 for(u32 fr=0;fr<frames;fr++){
  memcpy(out,bind,joints*48);memset(user,0,4096);
  u32 lo=0,hi=sets-1;while(lo+1<hi){u32 mid=(lo+hi)/2;if(fr<*(u16*)(frameTab+mid*4))hi=mid;else lo=mid;}
  u32 base=*(u16*)(frameTab+lo*4),count=*(u16*)(frameTab+lo*4+2);
  u32 off=*(u32*)(dataTab+4+lo*8),sz=*(u16*)(dataTab+2+lo*8);
  u8*set=work+(((size_t)anim+off)&0x7f);if(sz)memcpy(set,anim+off,sz);
  int idx=(int)(fr-base);float alpha=0.f;if(count<(u32)idx){alpha=1.f;idx=(int)count;}
  decode(out,user,anim,set,(int)count,idx,alpha);
  if(fwrite(out,48,joints,f)!=joints)return 3;
 }
 fclose(f);printf("joints %u frames %u sets %u fps %.3f\n",joints,frames,sets,fps);
 return 0;
}
