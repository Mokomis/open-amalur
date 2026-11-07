#ifndef OA_WIN_ASSETS_H
#define OA_WIN_ASSETS_H
#include <stddef.h>
#include <stdint.h>
#include <sys/types.h>
typedef struct AAssetManager{char root[2048];}AAssetManager;
typedef struct AAsset AAsset;
enum{AASSET_MODE_UNKNOWN,AASSET_MODE_RANDOM,AASSET_MODE_STREAMING,AASSET_MODE_BUFFER};
AAsset *AAssetManager_open(AAssetManager*,const char*,int);
int AAsset_read(AAsset*,void*,size_t);
off_t AAsset_getLength(AAsset*);
off64_t AAsset_getLength64(AAsset*);
const void *AAsset_getBuffer(AAsset*);
void AAsset_close(AAsset*);
#endif
