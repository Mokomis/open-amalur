#include "oa_creation_draft.h"
#include <stdio.h>
#include <string.h>
#include <errno.h>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <fcntl.h>
#include <unistd.h>
#include <errno.h>
#endif
int oa_creation_draft_load(oa_creation_state *s,const char *path){
 unsigned char bytes[OA_CREATION_ENVELOPE_MAX+1];oa_creation_state candidate;size_t n;int ok;FILE *f;
 if(!s||!path)return 1;
 f=fopen(path,"rb");if(!f)return errno==ENOENT?2:1;n=fread(bytes,1,sizeof bytes,f);ok=!ferror(f);if(fclose(f))ok=0;
 if(!ok||n>OA_CREATION_ENVELOPE_MAX||oa_creation_deserialize(&candidate,bytes,n)!=OA_CREATION_OK||candidate.phase!=OA_CREATION_DRAFT)return 1;
 *s=candidate;return 0;
}
int oa_creation_draft_save(const oa_creation_state *s,const char *path){
 unsigned char bytes[OA_CREATION_ENVELOPE_MAX];size_t n;char tmp[1200];unsigned attempt;int count;
 if(!s||!path||s->phase!=OA_CREATION_DRAFT||oa_creation_serialize(s,bytes,sizeof bytes,&n)!=OA_CREATION_OK)return 1;
#ifdef _WIN32
 for(attempt=0;attempt<32;attempt++){
  HANDLE h;DWORD written=0;int ok;
  count=snprintf(tmp,sizeof tmp,"%s.tmp-%lu-%u",path,(unsigned long)GetCurrentProcessId(),attempt);if(count<0||(size_t)count>=sizeof tmp)return 1;
  h=CreateFileA(tmp,GENERIC_WRITE,0,NULL,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,NULL);
  if(h==INVALID_HANDLE_VALUE){if(GetLastError()==ERROR_FILE_EXISTS)continue;return 1;}
  ok=WriteFile(h,bytes,(DWORD)n,&written,NULL)&&written==n;
  if(ok)ok=FlushFileBuffers(h)!=0;if(!CloseHandle(h))ok=0;
  if(ok)ok=MoveFileExA(tmp,path,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)!=0;
  if(!ok)DeleteFileA(tmp);return !ok;
 }
#else
 for(attempt=0;attempt<32;attempt++){
  int fd,ok=1;size_t at=0;
  count=snprintf(tmp,sizeof tmp,"%s.tmp-%ld-%u",path,(long)getpid(),attempt);if(count<0||(size_t)count>=sizeof tmp)return 1;
  fd=open(tmp,O_WRONLY|O_CREAT|O_EXCL,0600);if(fd<0){if(errno==EEXIST)continue;return 1;}
  while(at<n){ssize_t k=write(fd,bytes+at,n-at);if(k<0&&errno==EINTR)continue;if(k<=0){ok=0;break;}at+=(size_t)k;}
  if(ok&&fsync(fd))ok=0;if(close(fd))ok=0;
  if(ok&&rename(tmp,path))ok=0;if(!ok)unlink(tmp);return !ok;
 }
#endif
 return 1;
}
