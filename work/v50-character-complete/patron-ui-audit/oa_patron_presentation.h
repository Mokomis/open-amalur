#ifndef OA_PATRON_PRESENTATION_H
#define OA_PATRON_PRESENTATION_H
#include <stdint.h>
typedef struct oa_patron_presentation {uint32_t buff_id;const char *choice,*deity_detail,*blessing_title,*blessing_description,*bonus_summary;} oa_patron_presentation;
/* Bonus text is a readable source-derived summary; labels/details/lore are original English. */
const oa_patron_presentation *oa_patron_presentation_find(uint32_t buff_id);
#endif
