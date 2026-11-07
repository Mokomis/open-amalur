#ifndef OPEM_EXPLORATION_INPUT_H
#define OPEM_EXPLORATION_INPUT_H
#include <android/input.h>
/* New Android exploration controls. No native game input IDs or Lua events. */
typedef struct exploration_input {
    int move_id,look_id,keyboard_device,pad_device;
    float move_origin_x,move_origin_y,move_x,move_y,look_x,look_y;
    float pad_x,pad_y,pad_look_x,pad_look_y,look_dx,look_dy;
    unsigned keys;
    int reset_requested,toggle_requested;
} exploration_input;
void exploration_input_clear(exploration_input *input);
int exploration_input_event(exploration_input *input,AInputEvent *event,int width,int height);
void exploration_input_axes(exploration_input *input,float *right,float *forward,float *yaw_rate,float *pitch_rate);
float exploration_ui_scale(int width,int height);
#endif
