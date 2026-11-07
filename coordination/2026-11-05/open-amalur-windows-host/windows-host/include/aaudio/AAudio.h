#pragma once
#include <stdint.h>
typedef struct AAudioStream AAudioStream;
typedef struct AAudioStreamBuilder AAudioStreamBuilder;
typedef int aaudio_data_callback_result_t;
typedef aaudio_data_callback_result_t(*oa_audio_cb)(AAudioStream*,void*,void*,int32_t);
#define AAUDIO_OK 0
#define AAUDIO_FORMAT_PCM_FLOAT 2
#define AAUDIO_PERFORMANCE_MODE_LOW_LATENCY 12
#define AAUDIO_CALLBACK_RESULT_CONTINUE 0
int AAudio_createStreamBuilder(AAudioStreamBuilder**);
void AAudioStreamBuilder_setFormat(AAudioStreamBuilder*,int);
void AAudioStreamBuilder_setChannelCount(AAudioStreamBuilder*,int);
void AAudioStreamBuilder_setSampleRate(AAudioStreamBuilder*,int);
void AAudioStreamBuilder_setPerformanceMode(AAudioStreamBuilder*,int);
void AAudioStreamBuilder_setDataCallback(AAudioStreamBuilder*,oa_audio_cb,void*);
int AAudioStreamBuilder_openStream(AAudioStreamBuilder*,AAudioStream**);
void AAudioStreamBuilder_delete(AAudioStreamBuilder*);
int AAudioStream_requestStart(AAudioStream*);
int AAudioStream_requestStop(AAudioStream*);
int AAudioStream_close(AAudioStream*);
int AAudioStream_getSampleRate(AAudioStream*);
int AAudioStream_getXRunCount(AAudioStream*);
