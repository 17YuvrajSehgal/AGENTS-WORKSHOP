// Positive controls that need native code.
//   locality a|b : column-major (a) vs row-major (b) traversal of a 4096x4096 int matrix
//   lock a|b     : 2 threads, one shared mutex-protected counter (a) vs
//                  per-thread counters merged at the end (b)
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define N 4096
#define ITERS 3000000

static int m[N][N];
static long shared;
static pthread_mutex_t mu = PTHREAD_MUTEX_INITIALIZER;

static void *locked(void *_) {
    for (long i = 0; i < ITERS; i++) {
        pthread_mutex_lock(&mu);
        shared++;
        pthread_mutex_unlock(&mu);
    }
    return 0;
}

static void *local(void *out) {
    long c = 0;
    for (long i = 0; i < ITERS; i++) c++;
    *(volatile long *)out = c;
    return 0;
}

int main(int argc, char **argv) {
    int b = argv[2][0] == 'b';
    if (!strcmp(argv[1], "locality")) {
        long s = 0;
        for (int i = 0; i < N; i++) for (int j = 0; j < N; j++) m[i][j] = i ^ j;
        for (int r = 0; r < 4; r++)
            for (int i = 0; i < N; i++)
                for (int j = 0; j < N; j++) s += b ? m[i][j] : m[j][i];
        printf("%ld\n", s);
    } else {
        pthread_t t[2];
        long out[2] = {0, 0};
        for (int k = 0; k < 2; k++)
            pthread_create(&t[k], 0, b ? local : locked, &out[k]);
        for (int k = 0; k < 2; k++) pthread_join(t[k], 0);
        printf("%ld\n", b ? out[0] + out[1] : shared);
    }
    return 0;
}
