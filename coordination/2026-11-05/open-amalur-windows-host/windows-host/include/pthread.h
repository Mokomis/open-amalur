#ifndef OA_WIN_PTHREAD_H
#define OA_WIN_PTHREAD_H
#include "desktop_compat.h"
#include <stdlib.h>
#include <process.h>
typedef HANDLE pthread_t;
typedef CRITICAL_SECTION pthread_mutex_t;
typedef CONDITION_VARIABLE pthread_cond_t;
typedef struct{void*(*fn)(void*);void *arg;}oa_thread_start;
static unsigned __stdcall oa_thread_entry(void *p){oa_thread_start s=*(oa_thread_start*)p;free(p);s.fn(s.arg);return 0;}
static int pthread_create(pthread_t *t,const void *a,void*(*fn)(void*),void *p){oa_thread_start *s=malloc(sizeof(*s));(void)a;if(!s)return 1;s->fn=fn;s->arg=p;*t=(HANDLE)_beginthreadex(NULL,0,oa_thread_entry,s,0,NULL);if(!*t)free(s);return *t?0:1;}
static int pthread_join(pthread_t t,void **r){(void)r;WaitForSingleObject(t,INFINITE);CloseHandle(t);return 0;}
static int pthread_mutex_init(pthread_mutex_t *m,const void *a){(void)a;InitializeCriticalSection(m);return 0;}
static int pthread_mutex_destroy(pthread_mutex_t *m){DeleteCriticalSection(m);return 0;}
static int pthread_mutex_lock(pthread_mutex_t *m){EnterCriticalSection(m);return 0;}
static int pthread_mutex_unlock(pthread_mutex_t *m){LeaveCriticalSection(m);return 0;}
static int pthread_cond_init(pthread_cond_t *c,const void *a){(void)a;InitializeConditionVariable(c);return 0;}
static int pthread_cond_destroy(pthread_cond_t *c){(void)c;return 0;}
static int pthread_cond_wait(pthread_cond_t *c,pthread_mutex_t *m){return SleepConditionVariableCS(c,m,INFINITE)?0:1;}
static int pthread_cond_signal(pthread_cond_t *c){WakeConditionVariable(c);return 0;}
static int pthread_cond_broadcast(pthread_cond_t *c){WakeAllConditionVariable(c);return 0;}
#endif
