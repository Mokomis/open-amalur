#ifndef OA_DESKTOP_COMPAT_H
#define OA_DESKTOP_COMPAT_H
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <mmsystem.h>
#include <stdint.h>
#include <time.h>
#include <sys/types.h>
#undef near
#undef far
#ifdef _MSC_VER
#define __attribute__(x)
#endif
#ifndef CLOCK_MONOTONIC
#define CLOCK_MONOTONIC 1
#endif
typedef int64_t off64_t;
int clock_gettime(int which,struct timespec *t);
#endif
