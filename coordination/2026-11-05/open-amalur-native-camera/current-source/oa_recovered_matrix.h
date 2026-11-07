// Recovered cs:15032 RVA/VA 0x00abc070. out = left * right (row-vector storage).
// Native SSE converts each float input to double, adds in sequence, then stores float.
#pragma once
static inline void oa_matrix_mul_abc070(float out[16], const float right[16], const float left[16]) {
#if defined(__clang__)
#pragma clang fp contract(off)
#endif
    // Caller provides separate output, as required by the original unrolled writes.
    for(int row=0;row<4;++row) for(int col=0;col<4;++col) {
        double value=(double)right[col]*(double)left[row*4] + (double)right[4+col]*(double)left[row*4+1];
        value=value+(double)right[8+col]*(double)left[row*4+2];
        value=value+(double)right[12+col]*(double)left[row*4+3];
        out[row*4+col]=(float)value;
    }
}
