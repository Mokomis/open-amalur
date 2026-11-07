/* dxbc_test.c <in.dxbc> <out.spv>: translate one shader for checking with spirv-val. */
#include "oa_dxbc.h"
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    FILE *f;
    long n;
    void *d;
    uint32_t *spv;
    size_t words;
    char err[256];
    oa_shader_info *info = malloc(sizeof(*info));
    if (argc < 3 || !(f = fopen(argv[1], "rb"))) return 2;
    fseek(f, 0, SEEK_END);
    n = ftell(f);
    fseek(f, 0, SEEK_SET);
    d = malloc((size_t)n);
    fread(d, 1, (size_t)n, f);
    fclose(f);
    if (!oa_dxbc_translate(d, (size_t)n, info, &spv, &words, err, sizeof(err))) {
        printf("FAIL %s: %s\n", argv[1], err);
        return 1;
    }
    f = fopen(argv[2], "wb");
    fwrite(spv, 4, words, f);
    fclose(f);
    return 0;
}
