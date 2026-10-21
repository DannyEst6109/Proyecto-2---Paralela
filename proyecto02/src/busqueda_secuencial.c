/* Proyecto 02, inciso 2. Busqueda secuencial: referencia para calcular el speedup. */
#define _POSIX_C_SOURCE 200809L
#include <time.h>
#include "busqueda.h"

#define USO "Uso: busqueda_secuencial [-f frase] [-l limite] [-t segundos] archivo.aes\n" \
    "  Prueba las claves 0..limite-1 (por defecto 4294967296)."

int main(int argc, char **argv) {
    Params p; const char *file; Dataset d = {0};
    init_params(&p, UINT64_C(1) << 32, 1, 0);
    if (!parse_params(argc, argv, &p, &file) || !load_dataset(file, &d) || !phrase_fits(&p, &d)) {
        fprintf(stderr, "%s\nArgumentos o archivo AES invalidos.\n", USO);
        return 1;
    }
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) { fputs("No se pudo crear el contexto AES.\n", stderr); return 1; }
    unsigned char plain[MAX_MESSAGE + 16];
    int plen = (int)strlen(p.phrase), status = 0, timed_out = 0;
    uint64_t found = NO_KEY, attempts = 0;
    double start = wall_seconds();
    for (uint64_t k = 0; k < p.limit; ++k) {
        int result = try_phrase(ctx, k, &d, plain, p.phrase, plen); ++attempts;
        if (result < 0) { fputs("Error de API AES.\n", stderr); status = 1; break; }
        if (result) { found = k; break; }
        /* El reloj se consulta cada 4096 claves para no distorsionar la medicion. */
        if (p.max_seconds && (attempts & 4095) == 0 && wall_seconds() - start >= (double)p.max_seconds) {
            timed_out = 1; break;
        }
    }
    double elapsed = wall_seconds() - start;
    if (!status) {
        print_report("secuencial", 1, found, attempts, elapsed, timed_out, ctx, &d, &p);
        status = found != NO_KEY ? 0 : (timed_out ? 3 : 2);
    }
    EVP_CIPHER_CTX_free(ctx);
    return status;
}
