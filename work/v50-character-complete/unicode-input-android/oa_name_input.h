#ifndef OA_NAME_INPUT_H
#define OA_NAME_INPUT_H
#include <android/native_activity.h>
#include <stddef.h>
typedef struct oa_name_input oa_name_input;
/* Owner/render-thread transport. Visible UI and committed profiles stay in Veil. */
oa_name_input *oa_name_input_open(ANativeActivity *);
void oa_name_input_close(oa_name_input *);
int oa_name_input_available(const oa_name_input *);
int oa_name_input_show(oa_name_input *,const char *utf8);
void oa_name_input_hide(oa_name_input *);
void oa_name_input_sync(oa_name_input *,const char *utf8);
/* Returns1 update,0 none; confirmed1 Done,-1 cancel,0 change. Empty editing text
 * is allowed; creator's original empty-confirm rule remains authoritative. */
int oa_name_input_poll(oa_name_input *,char *utf8,size_t capacity,int *confirmed);
#endif
