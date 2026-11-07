#include <stddef.h>
typedef long long off64_t;typedef struct AAssetManager{int unused;}AAssetManager;typedef struct AAsset{const void *bytes;off64_t size;}AAsset;
#define AASSET_MODE_BUFFER 3
AAsset *AAssetManager_open(AAssetManager*,const char*,int);off64_t AAsset_getLength64(AAsset*);const void *AAsset_getBuffer(AAsset*);void AAsset_close(AAsset*);
