// Counter sanity check: a loop with an exactly known instruction count.
// Each iteration retires exactly 2 user-space instructions (dec + jnz), so
// instructions:u(N=2e9) - instructions:u(N=1e9) must be 2e9.
#include <stdlib.h>

int main(int argc, char **argv) {
    unsigned long n = strtoul(argv[1], 0, 10);
    __asm__ volatile("1: dec %0\n\tjnz 1b" : "+r"(n));
    return 0;
}
