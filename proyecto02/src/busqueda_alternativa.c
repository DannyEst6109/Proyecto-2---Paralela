/* Proyecto 02, inciso 3. Estrategia alternativa: familias de claves con balanceo
 * dinamico y terminacion temprana.
 *
 *  - Las claves se agrupan en 4 familias (bajos, patrones, ASCII, barrido exhaustivo).
 *  - Cada familia se divide en bloques de `batch` claves. Un contador atomico por
 *    familia, alojado en el proceso 0 (ventana RMA), entrega el siguiente bloque.
 *  - El proceso p empieza por la familia p % 4; si se agota, toma bloques de las demas.
 *  - Quien halla la clave la avisa a los demas con MPI_Issend; el resto sondea con
 *    MPI_Test entre bloques y se detiene sin bloquearse.
 */
#include "busqueda_mpi.h"

#define USO "Uso: mpirun -np N busqueda_alternativa [-e] [-f frase] [-o offset] [-l claves_barrido] [-b lote] [-t segundos] archivo.aes\n" \
    "  -e: solo barrido, para comparar la distribucion sobre el mismo espacio de claves.\n" \
    "  offset: inicio del barrido exhaustivo de respaldo (por defecto 2^24, donde terminan los valores bajos).\n" \
    "  claves_barrido: claves a recorrer desde el offset (por defecto 2^63)."

enum { FAM_BAJOS, FAM_PATRONES, FAM_ASCII, FAM_BARRIDO, NUM_FAM };
static const char *const FAM_NOMBRE[NUM_FAM] = {
    "valores bajos", "patrones humanos", "texto ASCII", "barrido exhaustivo"
};
#define TAG_ENCONTRADA 77
#define SONDEO 4096                      /* claves entre consultas de MPI_Test y reloj */
#define BAJOS_TOTAL (UINT64_C(1) << 24)  /* 0 .. 16777215 */
#define ASCII_ALFABETO "abcdefghijklmnopqrstuvwxyz0123456789"
#define ASCII_BASE 36
#define ASCII_LONG_MAX 5

#define ANIO_INI 1940
#define ANIOS 91                         /* 1940..2030 */
#define FECHAS (ANIOS * 12 * 31)
#define REPETIDOS 190                    /* digito 0-9 repetido 1..19 veces */
#define POTENCIAS (64 * 3 + 20 * 3)      /* 2^k y 10^k, con -1, 0, +1 */
static const uint64_t CONSTANTES[] = {
    UINT64_C(0xDEADBEEF), UINT64_C(0xCAFEBABE), UINT64_C(0xCAFED00D), UINT64_C(0xFEEDFACE),
    UINT64_C(0x0BADC0DE), UINT64_C(0xFFFFFFFF), UINT64_C(0x0123456789ABCDEF),
    UINT64_C(0xFEDCBA9876543210)
};
#define NUM_CONST (sizeof CONSTANTES / sizeof CONSTANTES[0])
#define PATRONES_TOTAL (2 * FECHAS + REPETIDOS + POTENCIAS + NUM_CONST)

static uint64_t pow_u64(uint64_t base, int exp) {
    uint64_t r = 1;
    while (exp-- > 0) r *= base;
    return r;
}

/* Clave numero `i` (desde 0) de la familia de patrones humanos. */
static uint64_t key_patrones(uint64_t i) {
    if (i < FECHAS) {                    /* AAAAMMDD */
        uint64_t y = ANIO_INI + i / 372, m = 1 + (i / 31) % 12, dd = 1 + i % 31;
        return y * 10000 + m * 100 + dd;
    }
    i -= FECHAS;
    if (i < FECHAS) {                    /* DDMMAAAA */
        uint64_t y = ANIO_INI + i / 372, m = 1 + (i / 31) % 12, dd = 1 + i % 31;
        return dd * 1000000 + m * 10000 + y;
    }
    i -= FECHAS;
    if (i < REPETIDOS) {                 /* 7, 77, 777, ... */
        uint64_t digit = i / 19, n = 1 + i % 19;
        return digit * ((pow_u64(10, (int)n) - 1) / 9);
    }
    i -= REPETIDOS;
    if (i < POTENCIAS) {                 /* potencias +- 1 */
        uint64_t base = i < 64 * 3 ? 2 : 10, j = i < 64 * 3 ? i : i - 64 * 3;
        uint64_t v = pow_u64(base, (int)(j / 3));
        return j % 3 == 0 ? v - 1 : (j % 3 == 1 ? v : v + 1);
    }
    return CONSTANTES[i - POTENCIAS];
}

/* Cadenas de 1 a 5 caracteres de [a-z0-9] empacetadas como bytes (big endian). */
static uint64_t ascii_total(void) {
    uint64_t total = 0;
    for (int l = 1; l <= ASCII_LONG_MAX; ++l) total += pow_u64(ASCII_BASE, l);
    return total;
}
static uint64_t key_ascii(uint64_t i) {
    int length = 1; uint64_t n = ASCII_BASE;
    while (i >= n) { i -= n; ++length; n *= ASCII_BASE; }
    uint64_t key = 0, div = n / ASCII_BASE;
    for (int pos = 0; pos < length; ++pos, div /= ASCII_BASE)
        key = (key << 8) | (unsigned char)ASCII_ALFABETO[(i / div) % ASCII_BASE];
    return key;
}

static uint64_t family_count(int f, const Params *p) {
    switch (f) {
    case FAM_BAJOS: return BAJOS_TOTAL;
    case FAM_PATRONES: return PATRONES_TOTAL;
    case FAM_ASCII: return ascii_total();
    default: return p->limit;
    }
}
static uint64_t family_key(int f, uint64_t i, const Params *p) {
    switch (f) {
    case FAM_BAJOS: return i;
    case FAM_PATRONES: return key_patrones(i);
    case FAM_ASCII: return key_ascii(i);
    default: return p->offset + i;
    }
}

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank); MPI_Comm_size(MPI_COMM_WORLD, &size);
    Params p; Dataset d = {0};
    /* El barrido de respaldo arranca donde terminan los valores bajos (2^24). El
     * offset es configurable con -o para acotar mediciones, pero por defecto NO se
     * sintoniza a ninguna clave concreta: asi la ventaja medida proviene de las
     * familias heuristicas y del balanceo, no de conocer la clave de antemano. */
    init_params(&p, LIMITE_MAX, 65536, BAJOS_TOTAL);
    if (!mpi_setup(argc, argv, USO, &p, &d)) return mpi_finish(1);
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) mpi_fail("No se pudo crear el contexto AES.");
    unsigned char plain[MAX_MESSAGE + 16];
    int plen = (int)strlen(p.phrase);

    /* Un contador por familia, en la memoria expuesta por el proceso 0. */
    uint64_t counters[NUM_FAM] = {0}, blocks[NUM_FAM];
    for (int f = 0; f < NUM_FAM; ++f) {
        uint64_t n = family_count(f, &p);
        blocks[f] = n / p.batch + (n % p.batch != 0);
    }
    MPI_Win win;
    MPI_Win_create(rank == 0 ? counters : NULL, rank == 0 ? (MPI_Aint)sizeof counters : 0,
                   sizeof(uint64_t), MPI_INFO_NULL, MPI_COMM_WORLD, &win);
    MPI_Win_lock_all(MPI_MODE_NOCHECK, win);

    /* Aviso no bloqueante: cada proceso deja una recepcion abierta. */
    uint64_t note[2], notice[2] = {NO_KEY, 0};
    MPI_Request recv_req;
    MPI_Request *send_req = malloc((size_t)size * sizeof *send_req);
    if (!send_req) mpi_fail("No se pudieron reservar solicitudes MPI.");
    int nsend = 0, notified = 0;
    MPI_Irecv(note, 2, MPI_UINT64_T, MPI_ANY_SOURCE, TAG_ENCONTRADA, MPI_COMM_WORLD, &recv_req);

    uint64_t found = NO_KEY, found_family = 0, attempts[NUM_FAM] = {0};
    int exhausted[NUM_FAM] = {0}, timed_out = 0, done = 0;
    if (p.exhaustive_only)
        for (int f = 0; f < FAM_BARRIDO; ++f) exhausted[f] = 1;
    MPI_Barrier(MPI_COMM_WORLD);
    double start = MPI_Wtime();
    while (!done) {
        int taken = 0;
        for (int s = 0; s < NUM_FAM && !taken && !done; ++s) {
            int f = (rank + s) % NUM_FAM;
            if (exhausted[f]) continue;
            uint64_t one = 1, block;
            MPI_Fetch_and_op(&one, &block, MPI_UINT64_T, 0, f, MPI_SUM, win);
            MPI_Win_flush(0, win);
            if (block >= blocks[f]) { exhausted[f] = 1; continue; }
            taken = 1;
            uint64_t first = block * p.batch, last = first + p.batch, n = family_count(f, &p);
            if (last > n) last = n;
            for (uint64_t i = first; i < last; ++i) {
                uint64_t k = family_key(f, i, &p);
                int result = try_phrase(ctx, k, &d, plain, p.phrase, plen); ++attempts[f];
                if (result < 0) mpi_fail("Error de API AES.");
                if (result) {            /* avisar a todos y terminar */
                    found = k; found_family = (uint64_t)f; notice[0] = k; notice[1] = (uint64_t)f;
                    for (int r = 0; r < size; ++r)
                        if (r != rank) MPI_Issend(notice, 2, MPI_UINT64_T, r, TAG_ENCONTRADA,
                                                 MPI_COMM_WORLD, &send_req[nsend++]);
                    done = 1; break;
                }
                if ((attempts[f] % SONDEO) == 0) {
                    MPI_Test(&recv_req, &notified, MPI_STATUS_IGNORE);
                    if (notified) { done = 1; break; }
                    if (p.max_seconds && MPI_Wtime() - start >= (double)p.max_seconds) {
                        timed_out = 1; done = 1; break;
                    }
                }
            }
        }
        if (!taken) break;               /* todas las familias agotadas */
        if (!done) {                     /* sondeo tambien entre bloques */
            MPI_Test(&recv_req, &notified, MPI_STATUS_IGNORE);
            if (notified) done = 1;
            if (p.max_seconds && MPI_Wtime() - start >= (double)p.max_seconds) {
                timed_out = 1; done = 1;
            }
        }
    }
    /* Consenso final: si hubo aciertos simultaneos gana la clave menor. */
    uint64_t best, best_family, local_family = found != NO_KEY ? found_family : UINT64_MAX;
    uint64_t local_key = found;
    if (notified && found == NO_KEY) local_key = note[0];
    MPI_Allreduce(&local_key, &best, 1, MPI_UINT64_T, MPI_MIN, MPI_COMM_WORLD);
    if (notified && found == NO_KEY && note[0] == best) local_family = note[1];
    else if (local_key != best) local_family = UINT64_MAX;
    MPI_Allreduce(&local_family, &best_family, 1, MPI_UINT64_T, MPI_MIN, MPI_COMM_WORLD);
    double local_time = MPI_Wtime() - start, elapsed = 0;
    int any_timeout = 0;
    MPI_Reduce(&local_time, &elapsed, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Allreduce(&timed_out, &any_timeout, 1, MPI_INT, MPI_MAX, MPI_COMM_WORLD);

    /* Cancelar/completar la recepcion y drenar mientras progresan los envios.
     * Issend solo completa tras emparejar una recepcion. Asi los aciertos
     * simultaneos no dependen del buffer eager ni bloquean MPI_Waitall.
     */
    if (!notified) {
        MPI_Cancel(&recv_req);
        MPI_Wait(&recv_req, MPI_STATUS_IGNORE);
    }
    for (int all_complete = 0; !all_complete;) {
        for (int flag = 1; flag;) {
            MPI_Iprobe(MPI_ANY_SOURCE, TAG_ENCONTRADA, MPI_COMM_WORLD, &flag, MPI_STATUS_IGNORE);
            if (flag) MPI_Recv(note, 2, MPI_UINT64_T, MPI_ANY_SOURCE, TAG_ENCONTRADA,
                              MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        }
        int complete = 1;
        if (nsend) MPI_Testall(nsend, send_req, &complete, MPI_STATUSES_IGNORE);
        MPI_Allreduce(&complete, &all_complete, 1, MPI_INT, MPI_MIN, MPI_COMM_WORLD);
    }
    free(send_req);
    MPI_Win_unlock_all(win);
    MPI_Win_free(&win);

    uint64_t per_family[NUM_FAM], total = 0;
    MPI_Reduce(attempts, per_family, NUM_FAM, MPI_UINT64_T, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0) {
        for (int f = 0; f < NUM_FAM; ++f) total += per_family[f];
        print_report("alternativa (familias, balanceo dinamico, Open MPI)", size, best, total,
                     elapsed, any_timeout && best == NO_KEY, ctx, &d, &p);
        for (int f = 0; f < NUM_FAM; ++f)
            printf("  Familia %-17s: %" PRIu64 " claves\n", FAM_NOMBRE[f], per_family[f]);
        if (best != NO_KEY) printf("Familia de la clave: %s\n", FAM_NOMBRE[best_family]);
    }
    EVP_CIPHER_CTX_free(ctx);
    return mpi_finish(best != NO_KEY ? 0 : (any_timeout ? 3 : 2));
}
