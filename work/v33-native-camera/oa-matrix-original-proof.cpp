#include <windows.h>
#include <cstdio>
#include <vector>
#include <cstring>
#include "oa_recovered_matrix.h"
static std::vector<unsigned char> read(const char*p){FILE*f=fopen(p,"rb");if(!f)return {};fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);std::vector<unsigned char>b(n);fread(b.data(),1,n,f);fclose(f);return b;}
int main(int argc,char**argv){
 if(argc!=4)return 2;auto code=read(argv[1]);auto cases=read(argv[2]);
 if(code.size()!=1618 || cases.empty() || cases.size()%128)return 3;
 void* page=VirtualAlloc(nullptr,code.size(),MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);if(!page)return 4;
 memcpy(page,code.data(),code.size());DWORD old=0;if(!VirtualProtect(page,code.size(),PAGE_EXECUTE_READ,&old))return 5;
 FlushInstructionCache(GetCurrentProcess(),page,code.size());
 typedef void(__thiscall *Fn)(float*,const float*,const float*);Fn original=(Fn)page;
 FILE*f=fopen(argv[3],"wb");if(!f)return 6;unsigned different=0,count=0;
 for(size_t pos=0;pos<cases.size();pos+=128){float inputs[32],want[16],got[16];memcpy(inputs,cases.data()+pos,128);original(want,inputs,inputs+16);oa_matrix_mul_abc070(got,inputs,inputs+16);if(memcmp(got,want,64)){++different;if(different<4)printf("Mismatch case %u\n",count);}fwrite(want,1,64,f);++count;}
 fclose(f);VirtualFree(page,0,MEM_RELEASE);printf("Original x86 comparison: %u cases, %u output bytes, %u mismatched cases\n",count,count*64,different);return different?1:0;
}
