#include "aes_comun.h"
/* Vector AES-128-GCM: clave, IV y texto de ceros (16 bytes de texto).
 * Caso de respuesta conocida con clave e IV de ceros.
 */
int main(void) {
    const unsigned char cipher[16] = {0x03,0x88,0xda,0xce,0x60,0xb6,0xa3,0x92,0xf3,0x28,0xc2,0xb9,0x71,0xb2,0xfe,0x78};
    const unsigned char tag[16] = {0xab,0x6e,0x47,0xd4,0x2c,0xec,0x13,0xbd,0xf5,0x3a,0x67,0xb2,0x12,0x57,0xbd,0xdf};
    unsigned char message[16] = {0}, plain[MAX_MESSAGE + 16];
    Dataset d = {0}; EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx || !encrypt_message(ctx, 0, message, 16, &d)
        || memcmp(d.cipher, cipher, 16) || memcmp(d.tag, tag, 16)
        || try_key(ctx, 0, &d, plain) != 1 || memcmp(plain, message, 16)) return 1;
    d.tag[0] ^= 1;
    if (try_key(ctx, 0, &d, plain) != 0) return 1;
    EVP_CIPHER_CTX_free(ctx);
    puts("PASS: vector AES-128-GCM y rechazo de etiqueta alterada.");
    return 0;
}
