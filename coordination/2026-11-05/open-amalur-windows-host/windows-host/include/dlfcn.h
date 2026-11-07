#pragma once
#include "desktop_compat.h"
#define RTLD_NOW 0
static void *dlopen(const char *n,int f){(void)f;return (void*)LoadLibraryA(n);}
static void *dlsym(void *h,const char *n){return h?(void*)GetProcAddress((HMODULE)h,n):NULL;}
