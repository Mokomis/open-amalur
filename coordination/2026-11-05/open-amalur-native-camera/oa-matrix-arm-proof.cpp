#include <cstdio>
#include <vector>
#include <cstring>
#include "oa_recovered_matrix.h"
static std::vector<unsigned char> read(const char*p){FILE*f=fopen(p,"rb");if(!f)return {};fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);std::vector<unsigned char>b(n);fread(b.data(),1,n,f);fclose(f);return b;}
int main(int argc,char**argv){if(argc!=3)return 2;auto cases=read(argv[1]),expected=read(argv[2]);if(cases.empty()||cases.size()%128||expected.size()!=cases.size()/2)return 3;unsigned count=0,different=0;for(size_t pos=0;pos<cases.size();pos+=128){float in[32],out[16];memcpy(in,cases.data()+pos,128);oa_matrix_mul_abc070(out,in,in+16);if(memcmp(out,expected.data()+pos/2,64))++different;++count;}printf("Recovered matrix proof: %u cases, %u mismatched cases\n",count,different);return different?1:0;}
