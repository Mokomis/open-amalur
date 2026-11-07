/* Recovered native wind path, static evidence; no target execution.
 * 00d079e0 initialize; 00c5f6d0 update; 00c5f770 EnvironmentMgr+0x28;
 * 00ff0c33 passes world simulation delta milliseconds; 00c8a680 palette.
 * Preserve captured wind.bin only when comparing the captured reference frame.
 */
#include <math.h>
#include <stdint.h>
typedef struct { float phase[8], vector[3]; } oa_native_wind;
static void oa_native_wind_init(oa_native_wind *w) {
    static const float initial[8]={0.0f,0.7853975296020508f,1.5707950592041016f,2.3561925888061523f,3.141590118408203f,3.926987648010254f,4.712385177612305f,5.4977827072143555f};
    for (int i=0;i<8;i++) w->phase[i]=initial[i];
    w->vector[0]=25.0f; w->vector[1]=w->vector[2]=0.0f;
}
static void oa_native_wind_step(oa_native_wind *w, uint32_t delta_ms) {
    float seconds=(float)((double)delta_ms*0.0010000000474974513);
    for(int i=0;i<8;i++) {
        float t=(float)((double)i/7.0);
        float rate=(float)((1.0-(double)t)*0.4000000059604645+(double)t*0.75);
        float angle=(float)((double)w->phase[i]+(double)rate*(double)seconds);
        w->phase[i]=(float)fmod((double)angle,6.283180236816406);
    }
}
static void oa_native_wind_palette(const oa_native_wind *w,float palette[64][4]) {
    for(int phase=0;phase<8;phase++) {
        float s=(float)sin((double)w->phase[phase]);
        for(int amp=0;amp<8;amp++) {
            float a=(float)((double)amp/7.0);
            for(int c=0;c<3;c++) palette[phase*8+amp][c]=w->vector[c]*s*a;
            palette[phase*8+amp][3]=1.0f;
        }
    }
}
/* Native tree-leaf palette00ca00e0 ->00a76770 ->00a75030. Time input is
 * uint32 millisecond clock, not delta. Five paired periods, ten scalar outputs.
 * Reproduces all ten saved reference values bit-for-bit at305493984ms.
 */
static void oa_native_leaf_palette(uint32_t time_ms,float palette[12]) {
    static const float base[5]={0.7099999785423279f,0.8899999856948853f,
        1.0099999904632568f,1.1299999952316284f,1.309999942779541f};
    for(int i=0;i<10;i++) {
        float period=(float)((double)base[i/2]*3.0);
        float phase=(i&1)?1.5707950592041016f:0.0f;
        float start=(float)((double)period*(double)phase/6.283180236816406);
        uint32_t offset=(uint32_t)((double)start*1000.0+0.5);
        uint32_t cycle=(uint32_t)((double)period*1000.0+0.5);
        uint32_t rem=(time_ms+offset)%cycle;
        float sec=(float)((double)rem*0.0010000000474974513);
        float angle=(float)(6.283180236816406*(double)sec/(double)period);
        float s=(float)sin((double)angle);
        palette[i]=(float)(0.5+(double)s*0.5);
    }
    palette[10]=palette[11]=0.0f;
}
/* Native step has no random wind direction/amplitude modulation. The recovered
 * default vector is (25,0,0), and captured displacement has this exact axis.
 * External setters/serialized overrides are not excluded by this bounded audit.
 * x87 sin/fmod extended precision can differ from this portable implementation.
 */
