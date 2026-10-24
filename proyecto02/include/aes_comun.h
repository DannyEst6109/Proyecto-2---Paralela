/* Laboratorio 03 - Carlos Daniel Estrada Vega, 20853. Utilidades AES-128 (ECB).
 * AES-128-ECB con PKCS#7 y HMAC-SHA256 sobre formato, longitud y cifrado.
 * Las claves numeradas son SOLO un espacio reducido para el experimento.
 */
#ifndef AES_COMUN_H
#define AES_COMUN_H
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/evp.h>
#include <openssl/hmac.h>
#define MAX_MESSAGE 4096
#define NO_KEY UINT64_MAX
#define AUTH_SIZE 32
typedef struct {
    unsigned char cipher[MAX_MESSAGE + 16];  /* texto cifrado (multiplo de 16 por el relleno) */
    int length;                              /* longitud del texto plano original */
    unsigned char tag[AUTH_SIZE];            /* autenticacion encrypt-then-MAC */
} Dataset;
/* Longitud del texto cifrado: PKCS#7 siempre agrega de 1 a 16 bytes de relleno. */
static inline int cipher_length(int plain_len) { return (plain_len / 16 + 1) * 16; }
static inline void make_key(uint64_t candidate, unsigned char key[16]) {
    memset(key, 0, 16);
    for (int i = 0; i < 8; ++i)
        key[15-i] = (unsigned char)(candidate >> (8*i));
}
static inline int parse_number(const char *s, uint64_t *value) {
    if (!s || !*s) return 0;
    for (const char *p = s; *p; ++p) if (*p < '0' || *p > '9') return 0;
    errno = 0;
    char *end;
    unsigned long long v = strtoull(s, &end, 10);
    if (errno || *end || v == UINT64_MAX) return 0;
    *value = (uint64_t)v;
    return 1;
}
/* Deriva una clave MAC separada por dominio y autentica la representacion binaria
 * canonica (version, longitud big endian y cifrado). No guarda el texto ni la clave.
 */
static inline int dataset_tag(uint64_t candidate, const Dataset *d, unsigned char tag[AUTH_SIZE]) {
    unsigned char key[16], mac_key[AUTH_SIZE], payload[8 + MAX_MESSAGE + 16];
    unsigned int n = 0;
    static const unsigned char domain[] = "Proyecto02/AESECB2/HMAC-SHA256";
    make_key(candidate, key);
    int ok = HMAC(EVP_sha256(), key, sizeof key, domain, sizeof domain - 1, mac_key, &n) != NULL
        && n == AUTH_SIZE;
    memcpy(payload, "ECB2", 4);
    for (int i = 0; i < 4; ++i) payload[7-i] = (unsigned char)((uint32_t)d->length >> (8*i));
    int clen = cipher_length(d->length);
    memcpy(payload + 8, d->cipher, (size_t)clen);
    if (ok) ok = HMAC(EVP_sha256(), mac_key, sizeof mac_key, payload, (size_t)clen + 8, tag, &n) != NULL
        && n == AUTH_SIZE;
    OPENSSL_cleanse(key, sizeof key);
    OPENSSL_cleanse(mac_key, sizeof mac_key);
    return ok;
}
/* 1 autentico; 0 clave/datos incorrectos; -1 error de biblioteca. */
static inline int verify_dataset(uint64_t candidate, const Dataset *d) {
    unsigned char expected[AUTH_SIZE];
    if (!dataset_tag(candidate, d, expected)) return -1;
    int ok = CRYPTO_memcmp(expected, d->tag, AUTH_SIZE) == 0;
    OPENSSL_cleanse(expected, sizeof expected);
    return ok;
}
static inline int encrypt_message(EVP_CIPHER_CTX *ctx, uint64_t candidate,
        const unsigned char *message, int length, Dataset *d) {
    unsigned char key[16]; int out = 0, tail = 0;
    make_key(candidate, key);
    d->length = length;
    return EVP_EncryptInit_ex(ctx, EVP_aes_128_ecb(), NULL, key, NULL) == 1
        && EVP_EncryptUpdate(ctx, d->cipher, &out, message, length) == 1
        && EVP_EncryptFinal_ex(ctx, d->cipher + out, &tail) == 1
        && out + tail == cipher_length(length)
        && dataset_tag(candidate, d, d->tag);
}
/* Descifra con relleno PKCS#7. Retorna 1 y la longitud del texto plano si el
 * autenticacion y relleno son validos, 0 si la clave/datos son incorrectos y -1 ante
 * un error de la biblioteca. Se usa para recuperar el archivo original.
 */
static inline int decrypt_message(EVP_CIPHER_CTX *ctx, uint64_t candidate,
        const Dataset *d, unsigned char plain[MAX_MESSAGE + 16], int *plain_len) {
    unsigned char key[16]; int out = 0, tail = 0;
    int clen = cipher_length(d->length);
    int auth = verify_dataset(candidate, d);
    if (auth != 1) return auth;
    make_key(candidate, key);
    if (EVP_DecryptInit_ex(ctx, EVP_aes_128_ecb(), NULL, key, NULL) != 1
        || EVP_DecryptUpdate(ctx, plain, &out, d->cipher, clen) != 1)
        return -1;
    if (EVP_DecryptFinal_ex(ctx, plain + out, &tail) != 1) {
        OPENSSL_cleanse(plain, (size_t)clen);
        return 0;
    }
    *plain_len = out + tail;
    return *plain_len == d->length;
}
static inline void print_hex(FILE *f, const unsigned char *data, int length) {
    for (int i = 0; i < length; ++i) fprintf(f, "%02x", data[i]);
    fputc('\n', f);
}
static inline int read_hex(FILE *f, unsigned char *data, int length) {
    for (int i = 0; i < length; ++i) {
        int a = fgetc(f), b = fgetc(f);
        if (!((a >= '0' && a <= '9') || (a >= 'a' && a <= 'f'))
            || !((b >= '0' && b <= '9') || (b >= 'a' && b <= 'f'))) return 0;
        a = a <= '9' ? a-'0' : a-'a'+10;
        b = b <= '9' ? b-'0' : b-'a'+10;
        data[i] = (unsigned char)((a << 4) | b);
    }
    return fgetc(f) == '\n';
}
static inline int save_dataset(const char *path, const Dataset *d) {
    FILE *f = fopen(path, "wb"); if (!f) return 0;
    fprintf(f, "AESECB2\n%d\n", d->length);
    print_hex(f, d->cipher, cipher_length(d->length));
    print_hex(f, d->tag, AUTH_SIZE);
    int ok = !ferror(f); if (fclose(f) != 0) ok = 0;
    return ok;
}
static inline int load_dataset(const char *path, Dataset *d) {
    FILE *f = fopen(path, "rb"); if (!f) return 0;
    char header[32], length[32]; uint64_t n = 0;
    int ok = fgets(header, sizeof header, f) && !strcmp(header, "AESECB2\n")
        && fgets(length, sizeof length, f);
    if (ok) {
        size_t l = strlen(length);
        ok = l > 0 && length[l-1] == '\n';
        if (ok) length[l-1] = 0;
        ok = ok && parse_number(length, &n) && n <= MAX_MESSAGE;
    }
    if (ok) {
        d->length = (int)n;
        ok = read_hex(f, d->cipher, cipher_length(d->length))
            && read_hex(f, d->tag, AUTH_SIZE) && fgetc(f) == EOF && !ferror(f);
    }
    fclose(f); return ok;
}
#endif
