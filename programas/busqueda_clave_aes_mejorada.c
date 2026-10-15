#define _POSIX_C_SOURCE 200809L
#include <time.h>
#include "aes_comun.h"
/* Mejoras propuestas por Carlos Daniel Estrada Vega, 20853. */
static double now(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) { perror("clock_gettime"); exit(1); }
    return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
}
int main(int argc, char **argv) {
    Dataset d = {0}; uint64_t number;
    if (argc < 4 || !parse_number(argv[3], &number)) {
        fprintf(stderr, "Uso:\n  %s preparar archivo clave [mensaje]\n  %s buscar archivo limite\n", argv[0], argv[0]);
        return 1;
    }
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) { fputs("No se pudo crear contexto AES.\n", stderr); return 1; }
    int status = 0;
    if (!strcmp(argv[1], "preparar") && (argc == 4 || argc == 5)) {
        const char *message = argc == 5 ? argv[4] : "Puedes lograrlo!";
        size_t length = strlen(message);
        if (!length || length > MAX_MESSAGE || RAND_bytes(d.nonce, 12) != 1
            || !encrypt_message(ctx, number, (const unsigned char *)message, (int)length, &d)
            || !save_dataset(argv[2], &d)) {
            fputs("Error al preparar datos (mensaje de 1 a 4096 bytes).\n", stderr); status = 1;
        } else printf("Datos AES-128-GCM guardados: %s\nLongitud: %zu bytes\nEl archivo no contiene la clave ni el texto original.\n", argv[2], length);
    } else if (!strcmp(argv[1], "buscar") && argc == 4 && number > 0 && number <= MAX_RANGE) {
        if (!load_dataset(argv[2], &d)) { fputs("Archivo AES invalido.\n", stderr); status = 1; }
        else {
            unsigned char plain[MAX_MESSAGE + 16]; uint64_t found = NO_KEY, attempts = 0;
            double start = now();
            for (uint64_t k = 0; k < number; ++k) {
                int result = try_key(ctx, k, &d, plain); ++attempts;
                if (result < 0) { fputs("Error de API AES.\n", stderr); status = 1; break; }
                if (result) { found = k; break; }
            }
            double elapsed = now() - start;
            if (!status) { print_result("secuencial mejorada", 1, found, attempts, elapsed, &d, plain); status = found == NO_KEY ? 2 : 0; }
        }
    } else { fputs("Argumentos invalidos. Limite permitido: 1 a 4294967296.\n", stderr); status = 1; }
    EVP_CIPHER_CTX_free(ctx); return status;
}
