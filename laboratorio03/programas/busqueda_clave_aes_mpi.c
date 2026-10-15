#include <mpi.h>
#include "aes_comun.h"
/* Carlos Daniel Estrada Vega, 20853: reparto por lotes y parada colectiva.
 * En ronda r, proceso p prueba [(r*n+p)*B, (r*n+p+1)*B).
 * Los intervalos son disjuntos y cubren [0, limite) al agotar el rango.
 */
int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, size; MPI_Comm_rank(MPI_COMM_WORLD, &rank); MPI_Comm_size(MPI_COMM_WORLD, &size);
    uint64_t limit = 0, batch = 4096; int valid = 1;
    Dataset d = {0};
    if (rank == 0) {
        valid = (argc == 3 || argc == 4) && parse_number(argv[2], &limit)
            && limit > 0 && limit <= MAX_RANGE;
        if (valid && argc == 4) valid = parse_number(argv[3], &batch) && batch > 0 && batch <= MAX_RANGE;
        if (valid) valid = load_dataset(argv[1], &d);
        if (!valid) fprintf(stderr, "Uso: %s archivo limite [lote]\nArchivo o argumentos invalidos.\n", argv[0]);
    }
    MPI_Bcast(&valid, 1, MPI_INT, 0, MPI_COMM_WORLD);
    if (!valid) { MPI_Finalize(); return 1; }
    MPI_Bcast(&limit, 1, MPI_UINT64_T, 0, MPI_COMM_WORLD);
    MPI_Bcast(&batch, 1, MPI_UINT64_T, 0, MPI_COMM_WORLD);
    MPI_Bcast(&d.length, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Bcast(d.nonce, 12, MPI_UNSIGNED_CHAR, 0, MPI_COMM_WORLD);
    MPI_Bcast(d.tag, 16, MPI_UNSIGNED_CHAR, 0, MPI_COMM_WORLD);
    MPI_Bcast(d.cipher, d.length, MPI_UNSIGNED_CHAR, 0, MPI_COMM_WORLD);
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) { fputs("Error al crear contexto AES.\n", stderr); MPI_Abort(MPI_COMM_WORLD, 1); return 1; }
    unsigned char plain[MAX_MESSAGE + 16];
    uint64_t found = NO_KEY, attempts = 0, total = 0;
    uint64_t stride = (uint64_t)size * batch;
    MPI_Barrier(MPI_COMM_WORLD);
    double start = MPI_Wtime();
    for (uint64_t base = 0; base < limit; base += stride) {
        uint64_t local = NO_KEY;
        uint64_t first = base + (uint64_t)rank * batch;
        uint64_t end = first + batch; if (end > limit) end = limit;
        for (uint64_t k = first; k < end; ++k) {
            int result = try_key(ctx, k, &d, plain); ++attempts;
            if (result < 0) { fputs("Error de API AES.\n", stderr); MPI_Abort(MPI_COMM_WORLD, 1); return 1; }
            if (result) { local = k; break; }
        }
        MPI_Allreduce(&local, &found, 1, MPI_UINT64_T, MPI_MIN, MPI_COMM_WORLD);
        if (found != NO_KEY) break;
    }
    double local_time = MPI_Wtime() - start, elapsed = 0;
    MPI_Reduce(&local_time, &elapsed, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    MPI_Reduce(&attempts, &total, 1, MPI_UINT64_T, MPI_SUM, 0, MPI_COMM_WORLD);
    if (rank == 0) {
        if (found != NO_KEY && try_key(ctx, found, &d, plain) != 1) {
            fputs("Fallo al verificar resultado.\n", stderr); MPI_Abort(MPI_COMM_WORLD, 1); return 1;
        }
        print_result("Open MPI", size, found, total, elapsed, &d, plain);
    }
    EVP_CIPHER_CTX_free(ctx); MPI_Finalize(); return found == NO_KEY ? 2 : 0;
}
