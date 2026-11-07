/* Standalone arithmetic probe: no PE entrypoint, imports, game startup, or
 * device access. Invokes only the reviewed pure Transform->matrix routine. */
#include <windows.h>
#include <cstdio>
#include <vector>
#include <cstring>
int main(int argc,char **argv){
 if(argc!=4)return 2;FILE *f=fopen(argv[1],"rb");if(!f)return 2;fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);if(n<4096||n>128*1024*1024)return 3;std::vector<unsigned char>b((size_t)n);if(fread(b.data(),1,b.size(),f)!=b.size())return 3;fclose(f);
 IMAGE_DOS_HEADER *dos=(IMAGE_DOS_HEADER*)b.data();if(dos->e_magic!=IMAGE_DOS_SIGNATURE||dos->e_lfanew<0||(size_t)dos->e_lfanew+sizeof(IMAGE_NT_HEADERS32)>b.size())return 3;
 IMAGE_NT_HEADERS32 *nt=(IMAGE_NT_HEADERS32*)(b.data()+dos->e_lfanew);if(nt->Signature!=IMAGE_NT_SIGNATURE||nt->FileHeader.Machine!=IMAGE_FILE_MACHINE_I386||nt->OptionalHeader.ImageBase!=0x400000||nt->OptionalHeader.SizeOfImage>128*1024*1024)return 3;
 unsigned char *image=(unsigned char*)VirtualAlloc(NULL,nt->OptionalHeader.SizeOfImage,MEM_RESERVE|MEM_COMMIT,PAGE_READWRITE);if(!image)return 4;
 memcpy(image,b.data(),nt->OptionalHeader.SizeOfHeaders);IMAGE_SECTION_HEADER *section=IMAGE_FIRST_SECTION(nt);
 for(unsigned i=0;i<nt->FileHeader.NumberOfSections;i++){if((size_t)section[i].PointerToRawData+section[i].SizeOfRawData>b.size()||(size_t)section[i].VirtualAddress+section[i].SizeOfRawData>nt->OptionalHeader.SizeOfImage)return 3;memcpy(image+section[i].VirtualAddress,b.data()+section[i].PointerToRawData,section[i].SizeOfRawData);}
 typedef void (__fastcall *matrix_fn)(void*,void*,float*);matrix_fn matrix=(matrix_fn)(image+0xac3a70-0x400000);
 f=fopen(argv[2],"rb");if(!f)return 2;unsigned count=0,fixups=0;if(fread(&count,4,1,f)!=1||count>1024||fread(&fixups,4,1,f)!=1||fixups>128)return 3;
 for(unsigned i=0;i<fixups;i++){unsigned offset;if(fread(&offset,4,1,f)!=1||offset>=0xac443a-0xac3a70-4)return 3;DWORD *p=(DWORD*)(image+0xac3a70-0x400000+offset);*p+=(DWORD)image-0x400000;}
 DWORD previous;if(!VirtualProtect(image,nt->OptionalHeader.SizeOfImage,PAGE_EXECUTE_READ,&previous))return 4;FlushInstructionCache(GetCurrentProcess(),image,nt->OptionalHeader.SizeOfImage);
 FILE *out=fopen(argv[3],"wb");if(!out)return 2;fwrite(&count,4,1,out);
 for(unsigned i=0;i<count;i++){unsigned char transform[48]={0};float result[16]={0};if(fread(transform,45,1,f)!=1)return 3;matrix(transform,NULL,result);if(fwrite(result,sizeof(result),1,out)!=1)return 3;}
 fclose(f);if(fclose(out))return 3;VirtualFree(image,0,MEM_RELEASE);return 0;
}
