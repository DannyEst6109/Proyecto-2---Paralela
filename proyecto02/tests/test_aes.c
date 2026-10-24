/* Vector AES-128 de clave cero y bloque cero; regresiones de autenticacion. */
#include "aes_comun.h"
#include <assert.h>
int main(void) {
    const unsigned char expected[16] = {
        0x66,0xe9,0x4b,0xd4,0xef,0x8a,0x2c,0x3b,
        0x88,0x4c,0xfa,0x59,0xca,0x34,0x2b,0x2e
    };
    unsigned char input[16] = {0}, plain[MAX_MESSAGE + 16];
    Dataset data = {0}; int n = 0;
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    assert(ctx);
    assert(encrypt_message(ctx, 0, input, sizeof input, &data));
    assert(!memcmp(data.cipher, expected, sizeof expected));
    assert(decrypt_message(ctx, 0, &data, plain, &n) == 1);
    assert(n == 16 && !memcmp(plain, input, 16));
    assert(decrypt_message(ctx, 44, &data, plain, &n) == 0);
    data.cipher[0] ^= 1;
    assert(decrypt_message(ctx, 0, &data, plain, &n) == 0);
    EVP_CIPHER_CTX_free(ctx);
    puts("PASS: vector AES-128-ECB, recuperacion y autenticacion de clave/contenido.");
    return 0;
}
