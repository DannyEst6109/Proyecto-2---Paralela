/* Proyecto 02, incisos 2 y 3. Utilidades comunes de las busquedas por fuerza bruta:
 * validacion por frase, lectura de argumentos y reporte de resultados.
 */
#ifndef BUSQUEDA_H
#define BUSQUEDA_H
#include <time.h>
#include <unistd.h>
#include "aes_comun.h"

#define FRASE_DEFECTO "es una prueba de"
#define FRASE_MAX 64
#define LIMITE_MAX (UINT64_C(1) << 63)   /* evita desbordar sumas de claves */

/* Parametros numericos y de texto; no contiene punteros para poder enviarse con MPI_Bcast. */
typedef struct {
    uint64_t limit;        /* base/secuencial: claves [0, limit). alternativa: claves del barrido */
    uint64_t batch;        /* claves por lote o por bloque de trabajo */
    uint64_t offset;       /* alternativa: inicio del barrido de respaldo */
    uint64_t max_seconds;  /* 0 = sin limite de tiempo */
    char phrase[FRASE_MAX + 1];
} Params;

static inline void init_params(Params *p, uint64_t limit, uint64_t batch, uint64_t offset) {
    p->limit = limit; p->batch = batch; p->offset = offset; p->max_seconds = 0;
    snprintf(p->phrase, sizeof p->phrase, "%s", FRASE_DEFECTO);
}

/* Lee: programa [-f frase] [-l limite] [-b lote] [-o offset] [-t segundos] archivo.aes
 * Retorna 1 si todo es valido. Los valores no indicados conservan su valor inicial.
 */
static inline int parse_params(int argc, char **argv, Params *p, const char **file) {
    int opt, ok = 1;
    optind = 1; opterr = 0;
    while ((opt = getopt(argc, argv, "f:l:b:o:t:")) != -1) {
        switch (opt) {
        case 'f':
            if (!*optarg || strlen(optarg) > FRASE_MAX) ok = 0;
            else snprintf(p->phrase, sizeof p->phrase, "%s", optarg);
            break;
        case 'l': ok = ok && parse_number(optarg, &p->limit) && p->limit > 0 && p->limit <= LIMITE_MAX; break;
        case 'b': ok = ok && parse_number(optarg, &p->batch) && p->batch > 0 && p->batch <= (UINT64_C(1) << 32); break;
        case 'o': ok = ok && parse_number(optarg, &p->offset) && p->offset <= LIMITE_MAX; break;
        case 't': ok = ok && parse_number(optarg, &p->max_seconds); break;
        default: ok = 0;
        }
    }
    if (!ok || optind != argc - 1) return 0;
    *file = argv[optind];
    return 1;
}

/* Cuenta ocurrencias de la frase (busqueda ingenua; los textos miden hasta 4096 bytes). */
static inline int contains_phrase(const unsigned char *text, int length, const char *phrase, int plen) {
    for (int i = 0; i + plen <= length; ++i)
        if (!memcmp(text + i, phrase, (size_t)plen)) return 1;
    return 0;
}

/* Descifra con la candidata y busca la frase. La unica comprobacion es la frase,
 * como pide el enunciado. Se desactiva el relleno PKCS#7 para descifrar bloques
 * en bruto: asi una clave incorrecta no provoca un error de relleno, solo texto
 * basura donde la frase no aparece. Retorna 1 si la contiene, 0 si no y -1 ante
 * un error de la API.
 */
static inline int try_phrase(EVP_CIPHER_CTX *ctx, uint64_t candidate, const Dataset *d,
        unsigned char plain[MAX_MESSAGE + 16], const char *phrase, int plen) {
    unsigned char key[16]; int out = 0;
    make_key(candidate, key);
    if (EVP_DecryptInit_ex(ctx, EVP_aes_128_ecb(), NULL, key, NULL) != 1
        || EVP_CIPHER_CTX_set_padding(ctx, 0) != 1
        || EVP_DecryptUpdate(ctx, plain, &out, d->cipher, cipher_length(d->length)) != 1)
        return -1;
    return contains_phrase(plain, out, phrase, plen);
}

/* La frase debe poder aparecer en el mensaje cifrado cargado. */
static inline int phrase_fits(const Params *p, const Dataset *d) {
    return (int)strlen(p->phrase) <= d->length;
}

static inline double wall_seconds(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC, &t)) { perror("clock_gettime"); exit(1); }
    return (double)t.tv_sec + (double)t.tv_nsec / 1e9;
}

/* Reporte comun. Tras hallar la clave se descifra para mostrar el mensaje. */
static inline void print_report(const char *mode, int processes, uint64_t found,
        uint64_t attempts, double elapsed, int timed_out, EVP_CIPHER_CTX *ctx,
        const Dataset *d, const Params *p) {
    unsigned char plain[MAX_MESSAGE + 16] = {0};
    printf("Ejecucion: %s | Procesos: %d\n", mode, processes);
    printf("Frase de busqueda: \"%s\"\n", p->phrase);
    printf("Claves probadas: %" PRIu64 "\n", attempts);
    if (found != NO_KEY) {
        unsigned char key[16]; make_key(found, key);
        try_phrase(ctx, found, d, plain, p->phrase, (int)strlen(p->phrase));
        printf("Clave encontrada: %" PRIu64 "\nClave AES (hex): ", found);
        print_hex(stdout, key, 16);
        printf("Mensaje: "); fwrite(plain, 1, (size_t)d->length, stdout); putchar('\n');
    } else if (timed_out) printf("Tiempo limite alcanzado (%" PRIu64 " s) sin hallar la clave.\n", p->max_seconds);
    else puts("No se encontro la clave en el rango.");
    printf("Tiempo de busqueda: %.9f segundos\n", elapsed);
    if (elapsed > 0) printf("Rendimiento: %.0f claves/s\n", (double)attempts / elapsed);
}
#endif
