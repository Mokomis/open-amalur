#ifndef _GNU_SOURCE
#define _GNU_SOURCE 1
#endif
#include "oa_cpu_policy.h"
#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#include <sys/resource.h>
#if defined(__linux__)
#include <sched.h>
#endif
#endif
unsigned oa_cpu_stream_workers(unsigned available,int requested){
 unsigned spare,n;if(!available)available=1;
 /* Half the spare logical CPUs, capped: rendering, audio and other services
  * retain headroom. One background reader still works on 1/2-core targets. */
 spare=available>2?available-2:0;n=spare/2;if(n<1)n=1;
 if(requested>0)n=(unsigned)requested;
 if(n>OA_CPU_MAX_STREAM_WORKERS)n=OA_CPU_MAX_STREAM_WORKERS;
 if(n>available)n=available;return n;
}
unsigned oa_cpu_available(void){
#ifdef _WIN32
 DWORD_PTR process_mask=0,system_mask=0;unsigned n=0;
 if(GetProcessAffinityMask(GetCurrentProcess(),&process_mask,&system_mask)){
  while(process_mask){n+=(unsigned)(process_mask&1);process_mask>>=1;}if(n)return n;
 }
 {SYSTEM_INFO info;GetSystemInfo(&info);return info.dwNumberOfProcessors?info.dwNumberOfProcessors:1;}
#else
#if defined(__linux__)
 cpu_set_t allowed;unsigned n=0,i;
 if(sched_getaffinity(0,sizeof(allowed),&allowed)==0){
  for(i=0;i<CPU_SETSIZE;i++)if(CPU_ISSET(i,&allowed))n++;
  if(n)return n;
 }
#endif
 {long n=sysconf(_SC_NPROCESSORS_ONLN);return n>0?(unsigned)n:1;}
#endif
}
void oa_cpu_background_thread(void){
#ifdef _WIN32
 SetThreadPriority(GetCurrentThread(),THREAD_PRIORITY_BELOW_NORMAL);
#else
 /* Linux/Android priority applies to this calling thread. Best effort only. */
 setpriority(PRIO_PROCESS,0,5);
#endif
}
