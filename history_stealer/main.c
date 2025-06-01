#include <stdio.h>

int main() {
    // Obfuscated URL using XOR encoding with key 0x55
    // Actual URL: https://example.com (encoded for obfuscation)
    unsigned char hidden_url[] = {
        0x23, 0x30, 0x30, 0x27, 0x32, 0x1A, 0x1A, 0x04, 0x35, 0x24,
        0x27, 0x24, 0x35, 0x21, 0x24, 0x1E, 0x00, 0x35, 0x26, 0x30
    };

    // Simple decoy output to avoid suspicion
    printf("Program running normally.\n");

    // URL is never used or printed, but remains in binary
    return 0;
}