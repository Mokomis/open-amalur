#ifndef OA_CREATION_SOURCE_TABLES_H
#define OA_CREATION_SOURCE_TABLES_H
#include "oa_creation.h"
typedef struct oa_creation_color_view {const oa_creation_color_record *records;size_t count;} oa_creation_color_view;
typedef struct oa_creation_asset_row {uint32_t id,category,race_mask,sex_mask;} oa_creation_asset_row;
extern const oa_creation_source_type oa_creation_types_data[8];
extern const oa_creation_appearance oa_creation_presets_data[8][5];
extern const oa_creation_patron oa_creation_patrons_data[4][6];
extern const int16_t oa_creation_skills_data[4][9];
extern const oa_creation_color_view oa_creation_colors_data[8][8];
extern const oa_creation_asset_row oa_creation_assets_data[];
extern const size_t oa_creation_assets_count;
extern const uint32_t oa_creation_category_hashes[6];
#define OA_CREATION_SOURCE_CRC 0xa08d9075u
#endif
