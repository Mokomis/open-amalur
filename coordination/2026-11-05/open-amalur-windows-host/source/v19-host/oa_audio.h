#ifndef OA_AUDIO_H
#define OA_AUDIO_H
/* The game's sounds through AAudio. Sound files are the original MS ADPCM, decoded as they play.
 * Which sound plays on which event, and every level and range, is authored: the motion tables' sound events are not decoded. */
#include <stddef.h>
#include <stdint.h>
struct AAssetManager;
typedef struct oa_audio oa_audio;
typedef struct oa_audio_stats{unsigned voices,underruns;float mix_ms;}oa_audio_stats;
oa_audio *oa_audio_open(struct AAssetManager *assets);
void oa_audio_close(oa_audio *a);
void oa_audio_set_active(oa_audio *a,int active);
int oa_audio_group(const oa_audio *a,const char *name);
void oa_audio_listener(oa_audio *a,const float position[3],float yaw);
/* position NULL plays flat. range is where it fades out, in world units. */
void oa_audio_play(oa_audio *a,int group,const float position[3],float gain,float range);
void oa_audio_loop(oa_audio *a,int group,float gain);
void oa_audio_get_stats(oa_audio *a,oa_audio_stats *out);
/* Decodes one MS ADPCM block to 16 bit samples, one channel per step. Returns the frames written. */
int oa_adpcm_block(const uint8_t *block,int block_size,int channels,const int16_t coefs[][2],int16_t *out,int max_frames);
#endif
