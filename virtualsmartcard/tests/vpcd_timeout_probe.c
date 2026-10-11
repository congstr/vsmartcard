#include "../src/vpcd/vpcd.h"

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

int main(int argc, char **argv)
{
    struct vicc_ctx *ctx;
    unsigned char *atr = NULL;
    struct timespec before, after;
    ssize_t result;
    long elapsed_ms;

    if (argc != 3)
        return 2;
    if (strcmp(argv[1], "server") == 0)
        ctx = vicc_init(NULL, (unsigned short) atoi(argv[2]));
    else if (strcmp(argv[1], "client") == 0)
        ctx = vicc_init("127.0.0.1", (unsigned short) atoi(argv[2]));
    else
        return 2;
    if (!ctx)
        return 3;
    if (strcmp(argv[1], "server") == 0 && !vicc_connect(ctx, 5, 0)) {
        vicc_exit(ctx);
        return 4;
    }
    clock_gettime(CLOCK_MONOTONIC, &before);
    result = vicc_getatr(ctx, &atr);
    clock_gettime(CLOCK_MONOTONIC, &after);
    elapsed_ms = (after.tv_sec - before.tv_sec) * 1000 +
            (after.tv_nsec - before.tv_nsec) / 1000000;
    printf("result=%zd errno=%d elapsed_ms=%ld socket=%d\n",
            result, errno, elapsed_ms, ctx->client_sock);
    free(atr);
    vicc_exit(ctx);
    return result > 0 ? 0 : 1;
}
