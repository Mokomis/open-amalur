#ifndef OA_CREATION_LAYOUT_H
#define OA_CREATION_LAYOUT_H
/* Shared Veil creator geometry. Design units retain the existing 840px scale. */
typedef struct oa_creation_layout{
 float scale,x,y,controls_w,row_h,tabs_y,tab_w;
 float preview[4],toolbar_y,footer_y,summary_y;
}oa_creation_layout;
static inline void oa_creation_layout_get(int width,int height,oa_creation_layout *r){
 float s=(float)height/840.f,w=(float)width;
 r->scale=s;r->x=32*s;r->y=166*s;r->row_h=55*s;
 r->controls_w=w*.365f;if(r->controls_w>540*s)r->controls_w=540*s;
 r->tabs_y=96*s;r->tab_w=124*s;r->footer_y=730*s;
 r->preview[0]=r->x+r->controls_w+40*s;r->preview[1]=230*s;
 r->preview[2]=w-r->preview[0]-32*s;r->preview[3]=480*s;
 r->toolbar_y=720*s;r->summary_y=166*s;
}
#endif
