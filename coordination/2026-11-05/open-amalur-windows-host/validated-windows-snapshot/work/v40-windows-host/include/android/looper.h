#ifndef OA_WIN_LOOPER_H
#define OA_WIN_LOOPER_H
typedef struct ALooper ALooper;
#define ALOOPER_PREPARE_ALLOW_NON_CALLBACKS 1
ALooper *ALooper_prepare(int);
void ALooper_acquire(ALooper*);void ALooper_release(ALooper*);void ALooper_wake(ALooper*);
int ALooper_pollOnce(int,int*,int*,void**);
#endif
