/* Laboratorio 03 - Carlos Daniel Estrada Vega, 20853. Utilidades AES-128-GCM.
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
#include <openssl/rand.h>
#define MAX_MESSAGE 4096
#define NO_KEY UINT64_MAX
#define MAX_RANGE (UINT64_C(1) << 32)
typedef struct {
    unsigned char nonce[12], tag[16], cipher[MAX_MESSAGE];
    int length;
} Dataset;
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
static inline int encrypt_message(EVP_CIPHER_CTX *ctx, uint64_t candidate,
        const unsigned char *message, int length, Dataset *d) {
    unsigned char key[16]; int out = 0, tail = 0;
    make_key(candidate, key);
    d->length = length;
    return EVP_EncryptInit_ex(ctx, EVP_aes_128_gcm(), NULL, key, d->nonce) == 1
        && EVP_EncryptUpdate(ctx, d->cipher, &out, message, length) == 1
        && EVP_EncryptFinal_ex(ctx, d->cipher + out, &tail) == 1
        && out + tail == length
        && EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, 16, d->tag) == 1;
}
/* Retorna 1 si autentica, 0 para candidata incorrecta y -1 ante error de API.
 * Nunca se utiliza el texto provisional si falla la autenticacion.
 */
static inline int try_key(EVP_CIPHER_CTX *ctx, uint64_t candidate,
        const Dataset *d, unsigned char plain[MAX_MESSAGE + 16]) {
    unsigned char key[16]; int out = 0, tail = 0;
    make_key(candidate, key);
    if (EVP_DecryptInit_ex(ctx, EVP_aes_128_gcm(), NULL, key, d->nonce) != 1
        || EVP_DecryptUpdate(ctx, plain, &out, d->cipher, d->length) != 1
        || EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, 16, (void *)d->tag) != 1)
        return -1;
    if (EVP_DecryptFinal_ex(ctx, plain + out, &tail) != 1) {
        OPENSSL_cleanse(plain, (size_t)d->length);
        return 0;
    }
    return out + tail == d->length ? 1 : -1;
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
    fprintf(f, "AESLAB1\n%d\n", d->length);
    print_hex(f, d->nonce, 12); print_hex(f, d->tag, 16);
    print_hex(f, d->cipher, d->length);
    int ok = !ferror(f); if (fclose(f) != 0) ok = 0;
    return ok;
}
static inline int load_dataset(const char *path, Dataset *d) {
    FILE *f = fopen(path, "rb"); if (!f) return 0;
    char header[32], length[32]; uint64_t n = 0;
    int ok = fgets(header, sizeof header, f) && !strcmp(header, "AESLAB1\n")
        && fgets(length, sizeof length, f);
    if (ok) {
        size_t l = strlen(length);
        ok = l > 0 && length[l-1] == '\n';
        if (ok) length[l-1] = 0;
        ok = ok && parse_number(length, &n) && n > 0 && n <= MAX_MESSAGE;
    }
    if (ok) {
        d->length = (int)n;
        ok = read_hex(f, d->nonce, 12) && read_hex(f, d->tag, 16)
            && read_hex(f, d->cipher, d->length) && fgetc(f) == EOF && !ferror(f);
    }
    fclose(f); return ok;
}
static inline void print_result(const char *mode, int processes, uint64_t found,
        uint64_t attempts, double elapsed, const Dataset *d, const unsigned char *plain) {
    printf("Ejecucion: %s | Procesos: %d\n", mode, processes);
    printf("Candidatas probadas: %" PRIu64 "\n", attempts);
    if (found == NO_KEY) puts("No se encontro la clave en el rango.");
    else {
        unsigned char key[16]; make_key(found, key);
        printf("Clave encontrada: %" PRIu64 "\nClave AES (hex): ", found);
        print_hex(stdout, key, 16);
        printf("Mensaje: "); fwrite(plain, 1, (size_t)d->length, stdout); putchar('\n');
        puts("Autenticacion GCM: correcta");
    }
    printf("Tiempo de busqueda: %.9f segundos\n", elapsed);
}
#endif
